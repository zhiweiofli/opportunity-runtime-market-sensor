"""Narrow parsers for the ICI combined release and State Street SPY product HTML."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import re


class Blocked(ValueError):
    """A safe local source/quality diagnostic, never an upstream response body."""


class Node:
    def __init__(self, tag, attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c, Node) else c for c in self.children).split())

    def nodes(self, tag=None):
        if tag is None or self.tag == tag:
            yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.nodes(tag)


class Document(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.root = Node('root')
        self.stack = [self.root]
        try:
            self.feed(raw.decode('utf-8-sig'))
            self.close()
        except (UnicodeError, RecursionError):
            raise Blocked('无法解析来源HTML编码/结构。') from None

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if not any(n.tag in ('head', 'script', 'style') for n in self.stack):
            self.stack[-1].children.append(data)


def amount(text):
    value = text.strip().replace('\u2212', '-').replace('\ufeff', '')
    if value.startswith('(') and value.endswith(')'):
        value = '-'+value[1:-1]
    if not re.fullmatch(r'[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?', value):
        raise Blocked('金额/股数缺失或格式无效；不补零或猜单位。')
    try:
        result = Decimal(value.replace(',', ''))
    except InvalidOperation:
        raise Blocked('来源数字无效。') from None
    if not result.is_finite():
        raise Blocked('来源数字不是有限值。')
    return result


def canonical(value):
    return format(value.normalize(), 'f') if value else '0'


def date_text(value):
    value = ' '.join(value.replace(',', '').split())
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%B %d %Y', '%b %d %Y'):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise Blocked('来源日期缺失或无法识别。')


MONTH_DATE = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+[0-9]{1,2},?\s+[0-9]{4}'


def cells(row):
    return [c.text() for c in row.children if isinstance(c, Node) and c.tag in ('td', 'th')]


def parse_ici(raw):
    root = Document(raw).root
    headings = [n.text() for n in root.nodes() if n.tag in ('h1', 'h2')]
    titles = [h for h in headings if all(w in h.lower() for w in ('combined', 'flows', 'etf', 'net issuance'))]
    if not titles:
        raise Blocked('不是ICI合并流向发布；登录页/其他报表不能替代。')
    title = titles[0]
    remainder = root.text().split(title, 1)[1].strip()
    published = re.match(r'(?:Published(?:\s+on)?[: ]+)?('+MONTH_DATE+r'|[0-9]{4}-[0-9]{2}-[0-9]{2})\b', remainder)
    if not published:
        raise Blocked('无法定位发布日；不使用报告周或正文中的日期猜发布日期。')
    published_date = date_text(published.group(1))
    tables = []
    for table in root.nodes('table'):
        rows = [cells(r) for r in table.nodes('tr')]
        domestic = [r for r in rows if r and r[0].strip().lower() in ('domestic', 'domestic equity')]
        if domestic:
            tables.append((table, rows, domestic))
    if len(tables) != 1 or len(tables[0][2]) != 1:
        raise Blocked('Domestic equity表缺失/重复/分类发生变化。')
    table, rows, domestic = tables[0]
    if not any(r and r[0].lower() == 'equity' for r in rows):
        raise Blocked('无法确认Domestic属于Equity分类。')
    # These are the exact published units; never infer USD from a magnitude.
    ordered = list(root.nodes())
    unit_labels = [n.text() for n in ordered[:ordered.index(table)]
                   if re.fullmatch(r'(?:Millions|Billions|Thousands) of [A-Za-z ]{1,40}', n.text())]
    if not unit_labels or unit_labels[-1] != 'Millions of dollars':
        raise Blocked('合并周报单位不是明确的Millions of dollars。')
    header_candidates = [r for r in rows if sum(bool(re.fullmatch(r'[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}', x)) for x in r) >= 4]
    if len(header_candidates) != 1:
        raise Blocked('报告周表头缺失或不明确。')
    header = header_candidates[0]
    date_cells = [x for x in header if x]
    if any(not re.fullmatch(r'[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}', x) for x in date_cells):
        raise Blocked('报告周表头包含未识别日期/标签。')
    dates = [date_text(x) for x in date_cells]
    values = domestic[0][1:]
    if len(dates) != len(values) or len(set(dates)) != len(dates):
        raise Blocked('报告周重复或值数不一致。')
    facts = sorted([{'period_end': d, 'value_usd_million': canonical(amount(v))} for d, v in zip(dates, values)], key=lambda r: r['period_end'])
    if len(facts) < 4:
        raise Blocked('合并周报不足四个不同报告周。')
    return {'title': title, 'published_date': published_date, 'published_precision': 'date',
            'category': 'Domestic equity', 'unit': 'USD million', 'estimated': True,
            'revision_note': '同一发布内旧周可能修订；不是初值、实时或月度实际值。',
            'rows': facts, 'selected_rows': facts[-4:]}


def parse_spy(raw):
    root = Document(raw).root
    titles = [n.text() for n in root.nodes('h1')]
    if not any('SPY' in h and 'ETF Trust' in h and '500' in h for h in titles):
        raise Blocked('发行人产品身份不是SPY ETF Trust。')
    listing = None
    price = volume = market_date = None
    section = ''
    for node in root.nodes():
        if node.tag in ('h1', 'h2', 'h3'):
            section = node.text()
        if node.tag != 'table':
            continue
        rows = [cells(r) for r in node.nodes('tr')]
        if rows and {'Exchange', 'Trading Currency', 'Ticker'}.issubset(rows[0]):
            if len(rows) != 2 or len(rows[0]) != len(rows[1]):
                raise Blocked('上市身份表存在多行/冲突。')
            listing = dict(zip(rows[0], rows[1]))
        if not section.startswith('Fund Market Price as of '):
            continue
        match = re.fullmatch(r'Fund Market Price as of ('+MONTH_DATE+r'|[0-9]{4}-[0-9]{2}-[0-9]{2})', section)
        if not match or market_date is not None:
            raise Blocked('价格与成交股数的共同日期缺失或冲突。')
        market_date = date_text(match.group(1))
        for row in rows:
            if len(row) != 2:
                continue
            if row[0].startswith('Closing Price'):
                if price is not None or not row[1].startswith('$'):
                    raise Blocked('收盘价字段/美元单位冲突。')
                price = amount(row[1][1:])
            if row[0].startswith('Exchange Volume (Shares)'):
                if volume is not None:
                    raise Blocked('成交股数重复。')
                volume = amount(row[1])
    if (listing is None or listing.get('Ticker') != 'SPY' or listing.get('Exchange') != 'NYSE ARCA'
            or listing.get('Trading Currency') != 'USD'):
        raise Blocked('缺少已核对的SPY美国上市/交易币种事实。')
    if price is None or volume is None or market_date is None or price <= 0 or volume <= 0 or volume != volume.to_integral_value():
        raise Blocked('缺少同日有效价格和Exchange Volume (Shares)；NAV/AUM不可替代。')
    return {'ticker': 'SPY', 'exchange': listing['Exchange'], 'currency': 'USD',
            'price_date': market_date, 'volume_date': market_date,
            'price_usd': canonical(price), 'exchange_volume_shares': canonical(volume),
            'notional_proxy_usd': canonical(price * volume),
            'volume_scope': '发行人同一Fund Market Price区块的primary-exchange shares；不是全市场成交量。',
            'role': '相关类别观测载体，不是ICI类别复制、交易选择或成本/容量验收。'}
