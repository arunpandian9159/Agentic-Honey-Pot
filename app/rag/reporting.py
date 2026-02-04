"""
Performance Reporting for RAG system.
Generates human-readable reports on system performance.
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class PerformanceReporter:
    """Generate performance reports for RAG system."""
    
    def __init__(self, learning_system):
        self.learning_system = learning_system
    
    async def generate_daily_report(self) -> str:
        """Generate daily performance report."""
        analysis = await self.learning_system.analyze_performance()
        
        if "error" in analysis:
            return f"# Report Error\n\n{analysis['error']}"
        
        if analysis.get("total_conversations", 0) == 0:
            return "# AI Honeypot Report\n\nNo conversations recorded yet."
        
        report = f"""# AI Honeypot Daily Performance Report
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Overall Metrics
- **Total Conversations:** {analysis['total_conversations']}
- **Success Rate:** {analysis['success_rate']*100:.1f}%
- **Avg Intelligence Score:** {analysis['average_intelligence_score']:.2f}/10
- **Avg Messages/Conversation:** {analysis['average_message_count']:.1f}

## Top Performing Personas
"""
        
        top_personas = analysis.get('top_personas', {})
        if top_personas:
            for persona, score in sorted(
                top_personas.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                report += f"- {persona}: {score:.2f}/10\n"
        else:
            report += "- No persona data available yet\n"
        
        report += "\n## Most Successful Tactics\n"
        tactics = analysis.get('successful_tactics', [])
        if tactics:
            for i, tactic in enumerate(tactics[:5], 1):
                report += f"{i}. {tactic}\n"
        else:
            report += "- No tactics data available yet\n"
        
        report += "\n## Areas for Improvement\n"
        improvements = analysis.get('improvement_areas', [])
        if improvements:
            for improvement in improvements:
                report += f"- {improvement}\n"
        else:
            report += "- System performing optimally\n"
        
        return report
    
    async def generate_collection_report(self) -> str:
        """Generate report on RAG collection statistics."""
        stats = await self.learning_system.get_collection_stats()
        
        report = f"""# RAG Collection Statistics
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
        for collection, info in stats.items():
            if "error" in info:
                report += f"## {collection}\n- Error: {info['error']}\n\n"
            else:
                report += f"""## {collection}
- Points: {info.get('points_count', 0)}
- Vectors: {info.get('vectors_count', 0)}

"""
        
        return report
