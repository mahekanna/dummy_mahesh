"""
Pagination utilities
"""

import math

def paginate_results(items, page=1, page_size=20):
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Current page number (1-based)
        page_size: Number of items per page
    
    Returns:
        dict: Pagination result with items and metadata
    """
    # Validate inputs
    page = max(1, page)
    page_size = min(max(1, page_size), 100)  # Cap at 100 items per page
    
    total = len(items)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    # Calculate start and end indices
    start = (page - 1) * page_size
    end = start + page_size
    
    # Slice items
    page_items = items[start:end]
    
    return {
        'items': page_items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
        'start_index': start + 1 if page_items else 0,
        'end_index': start + len(page_items)
    }

def get_pagination_params(request):
    """
    Extract pagination parameters from request
    
    Args:
        request: Flask request object
    
    Returns:
        tuple: (page, page_size)
    """
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        
        # Validate
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        
        return page, page_size
    except (ValueError, TypeError):
        return 1, 20