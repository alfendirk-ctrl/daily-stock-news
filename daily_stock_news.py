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

# Portfolio tickers
PORTFOLIO = {
    'ADBE': 'Adobe',
    'COIN': 'Coinbase',
    'VWRL': 'VWRL (All-World ETF)',
    'SMH': 'VanEck Semiconductors',
    'NFLX': 'Netflix',
    'NVDA': 'Nvidia',
    'GOOGL': 'Alphabet',
    'ESPO': 'VanEck Gaming & Esports',
    'VOW3': 'Volkswagen',
    'SHELL': 'Shell',
    'SQ': 'Block',
    'AMZN': 'Amazon',
    'ORCL': 'Oracle',
    'PYPL': 'PayPal',
    'PLTR': 'Palantir',
    'QLYS': 'Qualys',
    'NKE': 'Nike',
    'SBUX': 'Starbucks',
    'DUOL': 'Duolingo',
    'NVO': 'Novo Nordisk ADR',
    'DIS': 'Walt Disney',
    'T': 'AT&T',
    'ULVR': 'Unilever',
    'PINS': 'Pinterest',
    'SNAP': 'Snap',
    'HPQ': 'HP Inc',
    'KO': 'Coca-Cola',
    'ALFEN': 'Alfen',
    'NIO': 'NIO ADR',
    'FIGMA': 'Figma',
    'FCEL': 'FuelCell Energy',
    'SPCE': 'Virgin Galactic',
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

def summarize_article(title, content):
    """Summarize article using Claude API."""
    if not content:
        return None

    try:
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": f"""Geef een korte, bondige samenvatting van dit artikel in Nederlands (max 2-3 zinnen).
Focus op wat het betekent voor beleggers. Wees direct en praktisch.

Titel: {title}

Inhoud: {content}

Samenvatting (zonder inleiding):"""
                }
            ]
        )
        summary = message.content[0].text.strip()
        return summary if summary else None
    except Exception as e:
        print(f"Error summarizing: {e}")
        return None

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

            # Fetch and summarize
            if item['link']:
                print(f"  📰 Summarizing: {title[:50]}...")
                content = fetch_article_content(item['link'])
                summary = summarize_article(title, content)
                item['summary'] = summary

            unique_items.append(item)
            seen_titles.add(item['title'])
            if len(unique_items) >= 5:
                break

    return unique_items

def fetch_portfolio_news():
    """Fetch news about portfolio stocks (last 24h)."""
    news_items = {}

    for ticker, company_name in PORTFOLIO.items():
        try:
            feed = feedparser.parse(f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}')

            for entry in feed.entries[:2]:
                pub_date = entry.get('published_parsed')
                if pub_date:
                    pub_datetime = datetime(*pub_date[:6])
                    if datetime.now() - pub_datetime < timedelta(hours=24):
                        title = entry.title.lower()
                        if any(kw in title for kw in ['earn', 'guidance', 'ipo', 'ceo', 'cfo', 'dividend', 'acquisition', 'merger', 'analyst', 'upgrade', 'downgrade', 'deal', 'lawsuit', 'sec', 'regulation', 'stock split']):
                            if ticker not in news_items:
                                # Fetch and summarize
                                link = entry.get('link', '')
                                print(f"  📰 Summarizing {ticker}: {entry.title[:50]}...")
                                content = fetch_article_content(link) if link else None
                                summary = summarize_article(entry.title, content)

                                news_items[ticker] = {
                                    'company': company_name,
                                    'title': entry.title,
                                    'summary': summary,
                                    'link': link,
                                }
                            break
        except Exception as e:
            pass

    return news_items

def generate_email_html(market_news, portfolio_news):
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
            summary = info.get('summary', info['title'])
            link = info.get('link', '#')

            html += f"""
        <div class="news-item">
            <div class="news-title">
                <span class="ticker">{ticker}</span> {info['company']}
            </div>
            <div class="news-summary">{summary}</div>
            <div class="news-source">
                <a href="{link}" class="link">Lees artikel →</a>
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
    print("🔄 Fetching market news...")
    market_news = fetch_market_news()
    print(f"   Found {len(market_news)} market news items\n")

    print("🔄 Fetching portfolio news...")
    portfolio_news = fetch_portfolio_news()
    print(f"   Found {len(portfolio_news)} portfolio news items\n")

    # Generate email
    today = datetime.now().strftime('%d %B %Y')
    subject = f"📌 Dagelijkse beursupdate – {today}"
    html_body = generate_email_html(market_news, portfolio_news)

    print("📧 Sending email...\n")

    # Send email
    if send_email('alfendirk@gmail.com', subject, html_body):
        print("\n✅ Daily stock news email sent successfully!")
    else:
        print("\n❌ Failed to send email")
        exit(1)

if __name__ == '__main__':
    main()
