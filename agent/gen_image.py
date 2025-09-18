import os
from loguru import logger

def save_graph_visualization(graph, filename_prefix: str = "graph", display_in_jupyter: bool = True):
    """
    Save graph visualization to PNG file and optionally display in Jupyter.
    
    Args:
        graph: LangGraph instance
        filename_prefix: Prefix for the output filename
        display_in_jupyter: Whether to display in Jupyter notebook
        
    Returns:
        str: Path to saved image file or None if failed
    """
    try:
        # Generate graph image
        graph_image = graph.get_graph().draw_mermaid_png()
        
        # Create images directory if it doesn't exist
        images_dir = os.path.join(os.path.dirname(__file__), "..", "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Save to file with timestamp
        import time
        timestamp = int(time.time())
        image_path = os.path.join(images_dir, f"{filename_prefix}_{timestamp}.png")
        
        with open(image_path, "wb") as f:
            f.write(graph_image)
        
        logger.info(f"Graph visualization saved to: {image_path}")
        
        # Display in Jupyter if available and requested
        if display_in_jupyter:
            try:
                from IPython.display import Image, display
                display(Image(graph_image))
            except ImportError:
                logger.info("IPython not available, skipping display")
        
        return image_path
        
    except Exception as e:
        logger.warning(f"Failed to save graph visualization: {e}")
        return None