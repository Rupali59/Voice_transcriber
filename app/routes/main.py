"""
Main routes for the Voice Transcriber application
"""

from flask import Blueprint, render_template, request, jsonify, Response
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main page"""
    # Track page view for analytics
    try:
        from app.services.analytics_service import analytics_service
        analytics_service.track_page_view('EchoScribe - AI-Powered Audio Transcription', '/')
    except:
        pass  # Analytics not critical for main functionality
    
    return render_template('index.html')

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    from flask import jsonify, current_app
    from datetime import datetime
    
    from app import get_transcription_service
    transcription_service = get_transcription_service()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_jobs': len(transcription_service.get_all_jobs())
    })

@main_bp.route('/robots.txt')
def robots_txt():
    """Serve robots.txt for SEO"""
    robots_content = """User-agent: *
Allow: /

# Sitemap
Sitemap: {}/sitemap.xml

# Crawl-delay for respectful crawling
Crawl-delay: 1

# Disallow admin areas
Disallow: /admin/
Disallow: /api/admin/
Disallow: /logs/
Disallow: /uploads/
Disallow: /transcriptions/

# Allow important pages
Allow: /
Allow: /about
Allow: /help
Allow: /privacy
Allow: /terms
""".format(request.url_root.rstrip('/'))
    
    return Response(robots_content, mimetype='text/plain')

@main_bp.route('/sitemap.xml')
def sitemap_xml():
    """Generate XML sitemap for SEO"""
    base_url = request.url_root.rstrip('/')
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
    
    <!-- Main Pages -->
    <url>
        <loc>{base_url}/</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    
    <url>
        <loc>{base_url}/about</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    
    <url>
        <loc>{base_url}/help</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
    
    <url>
        <loc>{base_url}/privacy</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
    
    <url>
        <loc>{base_url}/terms</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
    
</urlset>"""
    
    return Response(sitemap_content, mimetype='application/xml')

@main_bp.route('/about')
def about():
    """About page"""
    try:
        from app.services.analytics_service import analytics_service
        analytics_service.track_page_view('About EchoScribe', '/about')
    except:
        pass
    
    return render_template('about.html')

@main_bp.route('/help')
def help():
    """Help page"""
    try:
        from app.services.analytics_service import analytics_service
        analytics_service.track_page_view('Help & Support', '/help')
    except:
        pass
    
    return render_template('help.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    try:
        from app.services.analytics_service import analytics_service
        analytics_service.track_page_view('Privacy Policy', '/privacy')
    except:
        pass
    
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    try:
        from app.services.analytics_service import analytics_service
        analytics_service.track_page_view('Terms of Service', '/terms')
    except:
        pass
    
    return render_template('terms.html')
