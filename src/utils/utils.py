import pygame


def clamp(n: float, minn: float, maxn: float) -> float:
    """
    Clamps a number between two specified values.

    This function ensures that the input number 'n' falls within the specified range defined
    by 'minn' and 'maxn'. If 'n' is less than 'minn', it is set to 'minn'. If 'n' is greater
    than 'maxn', it is set to 'maxn'.

    :param n: The number to be clamped.
    :param minn: The minimum value of the range.
    :param maxn: The maximum value of the range.
    :return: The clamped value, ensuring it falls within the specified range.
    """
    return max(min(maxn, n), minn)


def get_mask(image: pygame.Surface) -> pygame.mask.Mask:
    """
    Get a mask for collision detection from a Pygame image.

    :param image: A Pygame Surface containing the image.
    :return: A collision mask representing the non-transparent parts of the image.
    """
    return pygame.mask.from_surface(image)


def pixel_collision(rect1: pygame.Rect, rect2: pygame.Rect, mask1: pygame.mask.Mask, mask2: pygame.mask.Mask) -> bool:
    """
    Check if two objects collide using pixel-level collision detection.

    :param rect1: A pygame Rect representing the bounding box of the first object.
    :param rect2: A pygame Rect representing the bounding box of the second object.
    :param mask1: A pygame Mask representing the collision mask of the first object.
    :param mask2: A pygame Mask representing the collision mask of the second object.
    :return: True if the objects collide, False otherwise.
    """
    # Calculate the overlapping region of the two rectangles
    rect = rect1.clip(rect2)

    # If there is no overlap between the rectangles, return False
    if rect.width == 0 or rect.height == 0:
        return False

    # Calculate the offset between the two objects
    offset = (rect2.x - rect1.x, rect2.y - rect1.y)

    # Use the 'overlap' function to check if the masks overlap
    return bool(mask1.overlap(mask2, offset))

