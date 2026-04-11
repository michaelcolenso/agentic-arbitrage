"""
Agentic Arbitrage Factory - Monitoring Dashboard

Simple terminal-based dashboard for monitoring the factory.
"""
import asyncio
import curses
from datetime import datetime
from typing import Dict, Any, List

from core.storage import Storage
from core.models import FactoryStats
from factory import ArbitrageFactory


class Dashboard:
    """Terminal-based monitoring dashboard"""
    
    def __init__(self):
        self.storage = Storage()
        self.factory = ArbitrageFactory()
        self.running = True
    
    def run(self):
        """Run the dashboard"""
        curses.wrapper(self._main_loop)
    
    def _main_loop(self, stdscr):
        """Main dashboard loop"""
        # Setup
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        
        while self.running:
            # Clear screen
            stdscr.clear()
            
            # Get current status
            try:
                status = self.factory.get_status()
            except Exception as e:
                status = {"error": str(e)}
            
            # Render dashboard
            self._render_header(stdscr)
            self._render_stats(stdscr, status, 2)
            self._render_opportunities(stdscr, status, 10)
            self._render_sites(stdscr, status, 20)
            self._render_footer(stdscr)
            
            # Refresh
            stdscr.refresh()
            
            # Check for quit
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                self.running = False
            
            # Sleep
            curses.napms(1000)
    
    def _render_header(self, stdscr):
        """Render header"""
        height, width = stdscr.getmaxyx()
        
        header = "🤖 AGENTIC ARBITRAGE FACTORY - DASHBOARD"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        stdscr.addstr(0, 0, "=" * (width - 1), curses.A_BOLD)
        stdscr.addstr(1, 0, header[:width-1], curses.A_BOLD | curses.A_UNDERLINE)
        stdscr.addstr(1, width - len(timestamp) - 1, timestamp)
    
    def _render_stats(self, stdscr, status: Dict, row: int):
        """Render statistics section"""
        height, width = stdscr.getmaxyx()
        
        stats = status.get("stats", {})
        
        stdscr.addstr(row, 0, "📊 PORTFOLIO STATS", curses.A_BOLD)
        stdscr.addstr(row + 1, 0, "-" * 40)
        
        lines = [
            f"Total Opportunities: {stats.get('total_opportunities', 0)}",
            f"Validated:           {stats.get('validated_opportunities', 0)}",
            f"Active Sites:        {stats.get('active_sites', 0)}",
            f"Winner Sites:        {stats.get('winner_sites', 0)}",
            f"Culled Sites:        {stats.get('culled_sites', 0)}",
            f"Success Rate:        {stats.get('success_rate', 0):.1f}%",
            f"Total MRR:          ${stats.get('total_mrr', 0):,.2f}",
            f"Portfolio Value:    ${stats.get('portfolio_value', 0):,.2f}",
        ]
        
        for i, line in enumerate(lines):
            if row + 2 + i < height - 3:
                stdscr.addstr(row + 2 + i, 2, line[:width-3])
    
    def _render_opportunities(self, stdscr, status: Dict, row: int):
        """Render opportunities section"""
        height, width = stdscr.getmaxyx()
        
        opportunities = status.get("opportunities", {})
        recent = status.get("recent_opportunities", [])
        
        col = 45 if width > 90 else 0
        
        stdscr.addstr(row, col, "📋 OPPORTUNITIES", curses.A_BOLD)
        stdscr.addstr(row + 1, col, "-" * 35)
        
        # Status counts
        y = row + 2
        for status_name, count in opportunities.items():
            if y < height - 3 and y < row + 8:
                stdscr.addstr(y, col + 2, f"{status_name}: {count}")
                y += 1
        
        # Recent opportunities
        if recent and y < height - 5:
            stdscr.addstr(y + 1, col, "Recent:", curses.A_DIM)
            for opp in recent[:3]:
                if y + 2 < height - 3:
                    text = f"  • {opp['niche'][:25]} ({opp['status']})"
                    stdscr.addstr(y + 2, col, text[:35])
                    y += 1
    
    def _render_sites(self, stdscr, status: Dict, row: int):
        """Render sites section"""
        height, width = stdscr.getmaxyx()
        
        sites = status.get("sites", {})
        recent = status.get("recent_sites", [])
        
        stdscr.addstr(row, 0, "🌐 SITES", curses.A_BOLD)
        stdscr.addstr(row + 1, 0, "-" * 40)
        
        # Status counts
        y = row + 2
        for status_name, count in sites.items():
            if y < height - 3 and y < row + 8:
                stdscr.addstr(y, 2, f"{status_name}: {count}")
                y += 1
        
        # Recent sites
        if recent and y < height - 5:
            stdscr.addstr(y + 1, 0, "Recent:", curses.A_DIM)
            for site in recent[:3]:
                if y + 2 < height - 3:
                    text = f"  • {site['name'][:25]} ({site['status']})"
                    stdscr.addstr(y + 2, 0, text[:40])
                    y += 1
    
    def _render_footer(self, stdscr):
        """Render footer"""
        height, width = stdscr.getmaxyx()
        
        footer = "Press 'q' to quit | 'r' to refresh"
        stdscr.addstr(height - 2, 0, "=" * (width - 1), curses.A_BOLD)
        stdscr.addstr(height - 1, 0, footer, curses.A_DIM)


class SimpleDashboard:
    """Simple non-curses dashboard for broader compatibility"""
    
    def __init__(self):
        self.storage = Storage()
        self.factory = ArbitrageFactory()
    
    def display(self):
        """Display dashboard"""
        status = self.factory.get_status()
        
        print("\n" + "="*70)
        print("🤖 AGENTIC ARBITRAGE FACTORY - STATUS")
        print("="*70)
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n🎚️ MODE: {status.get('mode', 'unknown')}")
        print(f"🎯 ACTIVE VERTICAL: {status.get('active_vertical', 'none')}")
        ready = status.get('ready_to_fund', False)
        print(f"💰 READY TO FUND: {'YES' if ready else 'NO'}")
        
        print("\n📊 PORTFOLIO STATS:")
        stats = status.get("stats", {})
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key:25s}: {value:>12.2f}")
            else:
                print(f"  {key:25s}: {value:>12}")
        
        print("\n📋 OPPORTUNITIES BY STATUS:")
        for status_name, count in status.get("opportunities", {}).items():
            if count > 0:
                print(f"  {status_name:25s}: {count:>12}")
        
        print("\n🌐 SITES BY STATUS:")
        for status_name, count in status.get("sites", {}).items():
            if count > 0:
                print(f"  {status_name:25s}: {count:>12}")
        
        print("\n📊 EVIDENCE COMPLETENESS:")
        completeness = status.get("evidence_completeness", 0)
        print(f"  Overall: {completeness*100:.0f}%")
        for etype, count in status.get("evidence_counts", {}).items():
            print(f"  {etype:20s}: {count:>8} records")
        
        print("\n🚀 DEPLOYMENT HEALTH:")
        health = status.get("deployment_health", {})
        print(f"  Deployed sites: {health.get('deployed_count', 0)}")
        print(f"  With live URL:  {health.get('with_url', 0)}")
        
        last_metrics = status.get("last_real_metrics_date")
        print(f"\n📈 LAST REAL METRICS: {last_metrics or 'None'}")
        
        if status.get("recent_opportunities"):
            print("\n🆕 RECENT OPPORTUNITIES:")
            for opp in status["recent_opportunities"][:5]:
                print(f"  • {opp['niche'][:30]:30s} ({opp['status']:12s}) score: {opp['validation_score']:.1f}")
        
        if status.get("recent_sites"):
            print("\n🌐 RECENT SITES:")
            for site in status["recent_sites"][:5]:
                url = site.get('url', 'N/A')
                print(f"  • {site['name'][:30]:30s} ({site['status']})")
                if url and url != 'N/A':
                    print(f"    {url}")
        
        print("\n" + "="*70)


def main():
    """Main entry point"""
    import sys
    
    # Check if curses is available
    try:
        import curses
        use_curses = True
    except ImportError:
        use_curses = False
    
    if use_curses and len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Use interactive curses dashboard
        dashboard = Dashboard()
        dashboard.run()
    else:
        # Use simple dashboard
        dashboard = SimpleDashboard()
        dashboard.display()


if __name__ == "__main__":
    main()
