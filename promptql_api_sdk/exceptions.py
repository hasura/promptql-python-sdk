"""
Exceptions for the PromptQL Natural Language API SDK.
"""


class PromptQLAPIError(Exception):
    """
    Exception raised for errors in the PromptQL API.
    
    This exception is raised when the API returns an error response or when
    there is an error parsing the API response.
    """
    pass
