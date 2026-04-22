#!/usr/bin/env python3
"""
Daily stock news emailer for portfolio.
Gathers news about portfolio stocks and market news, sends daily email via Gmail.
"""

import os
import smtplib
import feedparser
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote
import re

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

def fetch_market_news():
    """Fetch top market news from multiple sources (last 24h)."""
    news_items = []

    # Google News RSS - Markets
    try:
        feed = feedparser.parse('https://news.google.com/rss/topics/CAAqJAgKIh5CVVNIX0dueHZSRkFTVkhRPQ?hl=en&gl=US&ceid=US:en')
        for entry in feed.entries[:5]:
            pub_date = entry.get('published_parsed')
            if pub_date:
                pub_datetime = datetime(*pub_date[:6])
                if datetime.now() - pub_datetime < timedelta(hours=24):
                    news_items.append({
                        'title': entry.title,
                        'source': 'Google News',
                        'date': pub_datetime,
                        'relevance': 'market'
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
                        'source': 'MarketWatch',
                        'date': pub_datetime,
                        'relevance': 'market'
                    })
    except Exception as e:
        print(f"Error fetching MarketWatch: {e}")

    # Reuters Markets (if available)
    try:
        feed = feedparser.parse('https://feeds.reuters.com/reuters/businessNews')
        for entry in feed.entries[:5]:
            pub_date = entry.get('published_parsed')
            if pub_date:
                pub_datetime = datetime(*pub_date[:6])
                if datetime.now() - pub_datetime < timedelta(hours=24):
                    # Only include if it mentions markets/stocks/macro
                    if any(word in entry.title.lower() for word in ['stock', 'market', 'fed', 'ecb', 'inflation', 'earnings', 'economy']):
                        news_items.append({
                            'title': entry.title,
                            'source': 'Reuters',
                            'date': pub_datetime,
                            'relevance': 'market'
                        })
    except Exception as e:
        print(f"Error fetching Reuters: {e}")

    # Sort by date and return top 5 unique
    news_items.sort(key=lambda x: x['date'], reverse=True)
    seen_titles = set()
    unique_items = []
    for item in news_items:
        if item['title'] not in seen_titles:
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
            # Try Yahoo Finance RSS
            feed = feedparser.parse(f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}')

            for entry in feed.entries[:2]:  # Just check first 2 entries per stock
                pub_date = entry.get('published_parsed')
                if pub_date:
                    pub_datetime = datetime(*pub_date[:6])
                    if datetime.now() - pub_datetime < timedelta(hours=24):
                        # Filter for relevant keywords
                        title = entry.title.lower()
                        if any(keyword in title for keyword in ['earn', 'guidance', 'ipo', 'ceo', 'cfo', 'dividend', 'acquisition', 'merger', 'analyst', 'upgrade', 'downgrade', 'deal', 'lawsuit', 'sec', 'regulation', 'stock split']):
                            if ticker not in news_items:
                                news_items[ticker] = {
                                    'company': company_name,
                                    'news': entry.title
                                }
                            break
        except Exception as e:
            pass  # Skip on error

    return news_items

def generate_email_body(market_news, portfolio_news):
    """Generate email body in the specified format."""
    today = datetime.now().strftime('%d %B %Y')

    body = f"""Hallo,

Hier is de korte beursupdate van vandaag.

1) Belangrijk markt-/macro nieuws (Top 5)

"""

    # Market news
    if market_news:
        for i, news in enumerate(market_news[:5], 1):
            # Clean title
            title = news['title'].strip()
            # Remove source markers like "- Reuters" at the end
            title = re.sub(r'\s*-\s*(Reuters|Bloomberg|Reuters|MarketWatch|Google News|AP|AFP).*$', '', title)
            body += f"* {title}\n"
    else:
        body += "* Geen significant marktnieuws vandaag.\n"

    body += "\n2) Portfolio nieuws\n\n"

    # Portfolio news
    if portfolio_news:
        for ticker, info in portfolio_news.items():
            title = info['news'].strip()
            title = re.sub(r'\s*-\s*(Reuters|Bloomberg|Reuters|MarketWatch|Yahoo Finance).*$', '', title)
            body += f"* {info['company']} ({ticker}): {title}\n"
    else:
        body += "➡️ Geen belangrijk nieuws over portfolio-aandelen vandaag.\n"

    body += "\n3) Alerts / Actiepunten\n\n"
    body += "* 👀 Controleer je portefeuille op sterke marktbewegingen\n"
    body += "* ✅ Zorg dat je al je research up-to-date is\n"
    body += f"* 📅 Update van {today}\n"

    body += "\nGroet,\n—"

    return body

def send_email(to_email, subject, body):
    """Send email via Gmail SMTP."""
    gmail_user = os.getenv('GMAIL_USER')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_user or not gmail_app_password:
        print("ERROR: GMAIL_USER or GMAIL_APP_PASSWORD not set")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = gmail_user
        msg['To'] = to_email

        # Attach body
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Send via Gmail
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
    print(f"   Found {len(market_news)} market news items")

    print("🔄 Fetching portfolio news...")
    portfolio_news = fetch_portfolio_news()
    print(f"   Found {len(portfolio_news)} portfolio news items")

    # Generate email
    today = datetime.now().strftime('%d %B %Y')
    subject = f"📌 Dagelijkse beursupdate – {today}"
    body = generate_email_body(market_news, portfolio_news)

    print(f"\n📧 Composing email...\n")
    print(body)
    print("\n" + "="*60)

    # Send email
    if send_email('alfendirk@gmail.com', subject, body):
        print("\n✅ Daily stock news email sent successfully!")
    else:
        print("\n❌ Failed to send email")
        exit(1)

if __name__ == '__main__':
    main()
