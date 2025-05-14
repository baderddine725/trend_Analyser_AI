class ContentRecommender:
    def __init__(self):
        # Mock content templates
        self.templates = {
            'video': [
                {'type': 'tutorial', 'format': '60s explanation'},
                {'type': 'reaction', 'format': 'duet style'},
                {'type': 'showcase', 'format': 'before/after'}
            ],
            'image': [
                {'type': 'infographic', 'format': 'carousel'},
                {'type': 'meme', 'format': 'comparison'},
                {'type': 'quote', 'format': 'text overlay'}
            ]
        }

    def get_recommendations(self, trend_topic):
        # Basic recommendation logic
        recommendations = {
            'video_ideas': [],
            'image_ideas': [],
            'hashtags': [],
            'best_posting_times': ['9:00 AM', '3:00 PM', '7:00 PM']
        }
        
        # Generate video recommendations
        for template in self.templates['video']:
            recommendations['video_ideas'].append({
                'title': f"{template['type'].title()} about {trend_topic}",
                'format': template['format'],
                'estimated_engagement': 'High',
                'suggestion': f"Create a {template['format']} {template['type']} video about {trend_topic}"
            })

        # Generate image recommendations
        for template in self.templates['image']:
            recommendations['image_ideas'].append({
                'title': f"{template['type'].title()} for {trend_topic}",
                'format': template['format'],
                'estimated_engagement': 'Medium',
                'suggestion': f"Design a {template['format']} {template['type']} about {trend_topic}"
            })

        # Generate hashtag recommendations
        recommendations['hashtags'] = [
            f"#{trend_topic.replace(' ', '')}",
            f"#{trend_topic.replace(' ', '_')}",
            '#trending',
            '#viral',
            f"#{trend_topic}challenge"
        ]

        return recommendations
