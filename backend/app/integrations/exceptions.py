class IntegrationError(Exception):
    """Raised when a call to an external provider (GitHub/Jira/Slack) fails."""
