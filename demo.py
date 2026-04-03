"""
Agentic Arbitrage Factory - Demo Runner

Quick demonstration of the factory capabilities.
"""
import asyncio
from datetime import datetime

from factory import ArbitrageFactory


async def run_demo():
    """Run a complete factory demo"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     🤖 AGENTIC ARBITRAGE FACTORY - DEMO                              ║
║                                                                      ║
║     "Stop building websites. Build the machine that builds           ║
║      the websites."                                                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    factory = ArbitrageFactory()
    
    # Run full cycle
    result = await factory.run_full_cycle()
    
    # Show final status
    print("\n" + "="*70)
    print("🏭 FINAL FACTORY STATUS")
    print("="*70)
    
    status = factory.get_status()
    
    print(f"""
📊 PORTFOLIO OVERVIEW:
   • Total Opportunities: {status['stats']['total_opportunities']}
   • Validated: {status['stats']['validated_opportunities']}
   • Active Sites: {status['stats']['active_sites']}
   • Winners: {status['stats']['winner_sites']}
   • Culled: {status['stats']['culled_sites']}
   • Success Rate: {status['stats']['success_rate']:.1f}%

💰 MONETIZATION:
   • Total MRR: ${status['stats']['total_mrr']:,.2f}
   • Portfolio Value: ${status['stats']['portfolio_value']:,.2f}
""")
    
    if status['recent_sites']:
        print("🌐 DEPLOYED SITES:")
        for site in status['recent_sites']:
            print(f"   • {site['name']}")
            if site['url']:
                print(f"     URL: {site['url']}")
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70)
    print("""
Next steps:
  1. Run 'python factory.py continuous' for continuous operation
  2. Run 'python factory.py status' to check status anytime
  3. Check the database at data/factory.db for detailed records
""")


if __name__ == "__main__":
    asyncio.run(run_demo())
