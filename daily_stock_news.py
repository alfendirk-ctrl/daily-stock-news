#!/usr/bin/env python3
"""
Daily stock news emailer for portfolio.
Gathers news about portfolio stocks and market news, sends daily email via Gmail.
Includes AI-powered article summaries via Claude API.
"""

import os
import smtplib
import feedparser
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from bs4 import BeautifulSoup
from anthropic import Anthropic

# Portfolio with position sizes (%)
PORTFOLIO = {
    'ADBE': {'name': 'Adobe', 'pct': 5.7},
    'COIN': {'name': 'Coinbase', 'pct': 7.6},
    'VWRL': {'name': 'VWRL (All-World ETF)', 'pct': 8.5},
    'SMH': {'name': 'VanEck Semiconductors', 'pct': 4.3},
    'NFLX': {'name': 'Netflix', 'pct': 3.6},
    'NVDA': {'name': 'Nvidia', 'pct': 3.8},
    'GOOGL': {'name': 'Alphabet', 'pct': 4.8},
    'ESPO': {'name': 'VanEck Gaming & Esports', 'pct': 3.9},
    'VOW3': {'name': 'Volkswagen', 'pct': 3.7},
    'SHELL': {'name': 'Shell', 'pct': 3.0},
    'SQ': {'name': 'Block', 'pct': 2.8},
    'AMZN': {'name': 'Amazon', 'pct': 2.4},
    'ORCL': {'name': 'Oracle', 'pct': 2.8},
    'PYPL': {'name': 'PayPal', 'pct': 2.7},
    'PLTR': {'name': 'Palantir', 'pct': 1.9},
    'QLYS': {'name': 'Qualys', 'pct': 2.7},
    'NKE': {'name': 'Nike', 'pct': 1.9},
    'SBUX': {'name': 'Starbucks', 'pct': 1.9},
    'DUOL': {'name': 'Duolingo', 'pct': 1.8},
    'NVO': {'name': 'Novo Nordisk ADR', 'pct': 1.5},
    'DIS': {'name': 'Walt Disney', 'pct': 2.0},
    'T': {'name': 'AT&T', 'pct': 0.8},
    'ULVR': {'name': 'Unilever', 'pct': 1.8},
    'PINS': {'name': 'Pinterest', 'pct': 0.4},
    'SNAP': {'name': 'Snap', 'pct': 0.3},
    'HPQ': {'name': 'HP Inc', 'pct': 0.5},
    'KO': {'name': 'Coca-Cola', 'pct': 1.2},
    'ALFEN': {'name': 'Alfen', 'pct': 1.4},
    'NIO': {'name': 'NIO ADR', 'pct': 0.8},
    'FIGMA': {'name': 'Figma', 'pct': 0.4},
    'FCEL': {'name': 'FuelCell Energy', 'pct': 0.0},
    'SPCE': {'name': 'Virgin Galactic', 'pct': 0.0},
}

# Initialize Anthropic client
client = Anthropic()

def fetch_article_content(url):
    """Fetch and extract article content from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()

        return text[:2000] if len(text) > 100 else None
    except Exception as e:
        print(f"Error fetching article: {e}")
        return None

def analyze_stock_news(ticker, company_name, title, content, position_size_pct):
    """Analyze stock news as an investment advisor using Claude."""
    try:
        # Use title if no content available
        analysis_content = content if content else title

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": f"""Je bent een ervaren beleggingsadviseur. Analyseer dit nieuws over {company_name} ({ticker})
en geef praktisch advies. Je weet dat deze positie {position_size_pct}% van het portfolio is.

Titel: {title}

Artikel: {analysis_content}

Geef je analyse in dit format (max 4-5 zinnen):
1. Wat gebeurde er? (1 zin)
2. Impact voor beleggers: BULLISH / BEARISH / NEUTRAAL (+ korte uitleg, 1 zin)
3. Relevantie voor jouw positie (rekening houdend met {position_size_pct}% grootte): (1 zin)
4. Wat zou je moeten doen? (1 zin advies: HOLD/BUY/SELL/MONITOR)

Schrijf direct en praktisch, geen fluff."""
                }
            ]
        )
        analysis = message.content[0].text.strip()
        if analysis:
            return analysis
        else:
            print(f"Warning: Empty analysis for {ticker}")
            return f"Nieuws: {title}"
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return f"Nieuws: {title}"

def fetch_market_news():
    """Fetch top market news from multiple sources (last 24h)."""
    news_items = []

    # Google News RSS - Markets
    try:
        feed = feedparser.parse('https://news.google.com/rss/topics/CAAqJAgKIh5CVVNIX0dveHZSRkFTVkhRPQ?hl=en&gl=US&ceid=US:en')
        for entry in feed.entries[:5]:
            pub_date = entry.get('published_parsed')
            if pub_date:
                pub_datetime = datetime(*pub_date[:6])
                if datetime.now() - pub_datetime < timedelta(hours=24):
                    news_items.append({
                        'title': entry.title,
                        'link': entry.get('link', ''),
                        'source': 'Google News',
                        'date': pub_datetime,
                    })
    except Exception as e:
        print(f"Error fetching Google News: {e}")

    # MarketWatch top stories
    try:
        feed = feedparser.parse('https://feeds.marketwatch.com/marketwatch/topstories/')
        for entry in feed.entries[:5]:
            pub_date = entry.get('published_parsed')
            if pub_date:
                pub_datetime = datetime(*pub_date[:6])
                if datetime.now() - pub_datetime < timedelta(hours=24):
                    news_items.append({
                        'title': entry.title,
                        'link': entry.get('link', ''),
                        'source': 'MarketWatch',
                        'date': pub_datetime,
                    })
    except Exception as e:
        print(f"Error fetching MarketWatch: {e}")

    # Reuters
    try:
        feed = feedparser.parse('https://feeds.reuters.com/reuters/businessNews')
        for entry in feed.entries[:5]:
            pub_date = entry.get('published_parsed')
            if pub_date:
                pub_datetime = datetime(*pub_date[:6])
                if datetime.now() - pub_datetime < timedelta(hours=24):
                    if any(w in entry.title.lower() for w in ['stock', 'market', 'fed', 'ecb', 'inflation', 'earnings']):
                        news_items.append({
                            'title': entry.title,
                            'link': entry.get('link', ''),
                            'source': 'Reuters',
                            'date': pub_datetime,
                        })
    except Exception as e:
        print(f"Error fetching Reuters: {e}")

    # Sort and deduplicate
    news_items.sort(key=lambda x: x['date'], reverse=True)
    seen_titles = set()
    unique_items = []

    for item in news_items:
        if item['title'] not in seen_titles:
            title = item['title'].strip()
            title = re.sub(r'\s*-\s*(Reuters|Bloomberg|MarketWatch|Google News|AP|AFP|Yahoo|CNBC).*$', '', title)
            item['title'] = title

            # Fetch and summarize market news
            if item['link']:
                print(f"  📰 Summarizing: {title[:50]}...")
                content = fetch_article_content(item['link'])
                if content:
                    try:
                        msg = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=150,
                            messages=[{
                                "role": "user",
                                "content": f"""Geef een korte, bondige samenvatting van dit marktnieuws in Nederlands (max 2-3 zinnen).
Focus op wat het betekent voor beleggers. Wees direct en praktisch.

Titel: {title}

Inhoud: {content}

Samenvatting:"""
                            }]
                        )
                        item['summary'] = msg.content[0].text.strip()
                    except:
                        item['summary'] = title

            unique_items.append(item)
            seen_titles.add(item['title'])
            if len(unique_items) >= 5:
                break

    return unique_items

def fetch_portfolio_news(portfolio_positions):
    """Fetch and analyze portfolio news with advisor perspective."""
    news_items = {}

    # Strong keywords for material news only
    material_keywords = [
        'earnings beat', 'earnings miss', 'beat estimates', 'missed estimates',
        'guidance raised', 'guidance lowered', 'outlook increased', 'outlook cut',
        'ceo resigns', 'ceo replaced', 'cfo resigns', 'new ceo', 'new cfo',
        'acquisition', 'merger', 'acquired by', 'buyout',
        'bankruptcy', 'restructuring', 'debt concern',
        'analyst upgrade', 'analyst downgrade', 'price target',
        'lawsuit', 'sec investigation', 'regulatory',
        'dividend increase', 'dividend cut', 'stock split',
        'product launch', 'major deal', 'partnership', 'contract win',
        'market share', 'competitive threat'
    ]

    for ticker, company_info in PORTFOLIO.items():
        try:
            company_name = company_info['name']
            feed = feedparser.parse(f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}')

            for entry in feed.entries[:3]:
                pub_date = entry.get('published_parsed')
                if pub_date:
                    pub_datetime = datetime(*pub_date[:6])
                    if datetime.now() - pub_datetime < timedelta(hours=24):
                        title_lower = entry.title.lower()
                        # Only include truly material news
                        if any(kw in title_lower for kw in material_keywords):
                            if ticker not in news_items:
                                link = entry.get('link', '')
                                print(f"  📰 Analyzing {ticker}: {entry.title[:50]}...")
                                content = fetch_article_content(link) if link else None

                                # Get position size
                                position_pct = company_info.get('pct', 0)

                                # Analyze as advisor
                                analysis = analyze_stock_news(
                                    ticker, company_name, entry.title, content, position_pct
                                )

                                print(f"    Analysis result: {analysis[:50] if analysis else 'None'}...")

                                news_items[ticker] = {
                                    'company': company_name,
                                    'title': entry.title,
                                    'analysis': analysis if analysis else f"📰 {entry.title}",
                                    'link': link,
                                    'position_pct': position_pct,
                                }
                            break
        except Exception as e:
            pass

    return news_items

def generate_email_html(market_news, portfolio_news, portfolio_positions):
    """Generate HTML email body with better formatting."""
    today = datetime.now().strftime('%d %B %Y')

    html = f"""<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; font-size: 18px; }}
        .news-item {{ background: #f9f9f9; padding: 15px; margin-bottom: 15px; border-left: 4px solid #667eea; border-radius: 3px; }}
        .news-title {{ font-weight: bold; color: #333; margin-bottom: 8px; }}
        .news-summary {{ color: #555; margin-bottom: 8px; font-size: 14px; }}
        .news-source {{ color: #999; font-size: 12px; }}
        .ticker {{ background: #667eea; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 12px; }}
        .link {{ color: #667eea; text-decoration: none; font-size: 12px; }}
        .link:hover {{ text-decoration: underline; }}
        .footer {{ color: #999; font-size: 12px; margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; }}
        .empty {{ color: #999; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 Dagelijkse Beursupdate</h1>
        <p style="margin: 0; opacity: 0.9;">{today}</p>
    </div>

    <div class="section">
        <h2>📊 Belangrijk Markt- & Macronieuws</h2>
"""

    if market_news:
        for news in market_news[:5]:
            summary = news.get('summary', 'Geen samenvatting beschikbaar')
            link = news.get('link', '#')
            source = news.get('source', 'Bron onbekend')

            html += f"""
        <div class="news-item">
            <div class="news-title">{news['title']}</div>
            <div class="news-summary">{summary}</div>
            <div class="news-source">
                Bron: <strong>{source}</strong> | <a href="{link}" class="link">Lees meer →</a>
            </div>
        </div>
"""
    else:
        html += '<div class="empty">➡️ Geen significant marktnieuws vandaag.</div>'

    html += """
    </div>

    <div class="section">
        <h2>🎯 Portfolio Nieuws</h2>
"""

    if portfolio_news:
        for ticker, info in portfolio_news.items():
            analysis = info.get('analysis', info['title'])
            link = info.get('link', '#')
            position_pct = info.get('position_pct', 0)

            html += f"""
        <div class="news-item">
            <div class="news-title">
                <span class="ticker">{ticker}</span> {info['company']}
                <span style="font-size: 12px; color: #999; margin-left: 8px;">({position_pct}% portfolio)</span>
            </div>
            <div class="news-summary"><strong style="color: #667eea;">Adviseur analyse:</strong><br/>{analysis}</div>
            <div class="news-source">
                <a href="{link}" class="link">Lees originele artikel →</a>
            </div>
        </div>
"""
    else:
        html += '<div class="empty">➡️ Geen belangrijk nieuws over portfolio-aandelen vandaag.</div>'

    html += f"""
    </div>

    <div class="footer">
        <p>🔄 Update van {today} • Volgende update morgen om 20:00 UTC</p>
        <p>Tip: Zorg dat je deze e-mails niet mist door ze in een separate label op te slaan.</p>
    </div>
</body>
</html>
"""
    return html

def send_email(to_email, subject, html_body):
    """Send HTML email via Gmail SMTP."""
    gmail_user = os.getenv('GMAIL_USER')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_user or not gmail_app_password:
        print("ERROR: GMAIL_USER or GMAIL_APP_PASSWORD not set")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = gmail_user
        msg['To'] = to_email

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, to_email, msg.as_string())

        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def main():
    """Main function."""
    # Create portfolio positions dict for advisor context
    portfolio_positions = {ticker: info for ticker, info in PORTFOLIO.items()}

    print("🔄 Fetching market news...")
    market_news = fetch_market_news()
    print(f"   Found {len(market_news)} market news items\n")

    print("🔄 Fetching portfolio news...")
    portfolio_news = fetch_portfolio_news(portfolio_positions)
    print(f"   Found {len(portfolio_news)} portfolio news items\n")

    # Generate email
    today = datetime.now().strftime('%d %B %Y')
    subject = f"📌 Dagelijkse beursupdate – {today}"
    html_body = generate_email_html(market_news, portfolio_news, portfolio_positions)

    print("📧 Sending email...\n")

    # Send email
    if send_email('alfendirk@gmail.com', subject, html_body):
        print("\n✅ Daily stock news email sent successfully!")
    else:
        print("\n❌ Failed to send email")
        exit(1)

if __name__ == '__main__':
    main()
