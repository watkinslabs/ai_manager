from ai_manager.ai_manager import AIManager
from wl_config_manager  import ConfigManager



cm=ConfigManager("config.yaml")


aim=AIManager(cm.ai_manager)

"""
# Generate blog post with metadata
post = aim.chat('create_blog_post', {
    'topic': 'AI in Healthcare',
    'target_audience': 'medical professionals',
    'word_count': 1500
}, validate=False)
"""
# Generate blog post with metadata
post = aim.chat('project_discovery', {
    'user_request': 'i want an email inbox that will let me send emails on my website. a main page, a spam, a trash and the ability to have folders, read and unread, with many users and attachments.',
}, validate=True)



print(post)