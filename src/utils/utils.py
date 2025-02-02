import random
import pygame


def get_random_value(value: list | tuple, random_type: str = "auto", as_int: bool = False):
    """Returns a random value based on the specified random_type.

    - "range": Assumes `value` is (min, max) and picks a number in the range.
    - "choice": Assumes `value` is a list/tuple and picks one randomly.
    - "auto": Tries to guess (uses range if 2 numbers, picks one otherwise).
    - as_int: If True, forces integer selection from ranges.
    """
    if random_type == "range":
        if as_int:
            return random.randint(*value)
        elif isinstance(value[0], float) or isinstance(value[1], float):
            return random.uniform(*value)
        else:
            return random.randint(*value)  # default to int if no float detected

    elif random_type == "choice":
        return random.choice(value)

    else:
        # Auto-detect if not explicitly set
        if isinstance(value, (list, tuple)) and len(value) == 2 and all(isinstance(v, (int, float)) for v in value):
            if isinstance(value[0], float) or isinstance(value[1], float):
                return random.uniform(*value) if not as_int else random.randint(*value)
            return random.randint(*value)

    if isinstance(value, (list, tuple)):
        return random.choice(value)
    return value


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


def rotate_on_pivot(image, angle, pivot, origin):
    """
    Rotate an image around a pivot point.

    :param image: The Pygame image to be rotated.
    :param angle: The angle of rotation in degrees.
    :param pivot: The pivot point around which the image will be rotated.
    :param origin: The origin point of the image.
    :return: The rotated image and its bounding rectangle.
    """
    surf = pygame.transform.rotate(image, angle)

    offset = pivot + (origin - pivot).rotate(-angle)
    rect = surf.get_rect(center=offset)

    return surf, rect


def printc(*message, color="default", styles=None, end="\n"):
    """
    Print a message in color.
    :param message: The message to be printed.
    :param color: The color in which the message should be printed.
    :param styles: A list of styles to apply to the message.
    :param end: The string to print at the end.
    :return: None
    """
    color_codes = {
        "default": "\033[39m",
        "gray": "\033[37m",
        "black": "\033[90m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "pink": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "orange": "\033[38;5;208m",
    }
    style_codes = {
        "bold": "\033[1m",
        "dim": "\033[2m",
        "italic": "\033[3m",
        "underline": "\033[4m",
        "blink": "\033[5m",
        "reverse": "\033[7m",
    }
    reset_all_code = "\033[0m"

    if color not in color_codes:
        raise Exception(f"Invalid color specified. Options: {list(color_codes.keys())}")
    if styles is not None:
        for style in styles:
            if style not in style_codes:
                raise Exception(f"Invalid style specified. Options: {list(style_codes.keys())}")

    style_str = "".join([style_codes[style] for style in styles]) if styles is not None else ""
    print(*[f"{color_codes[color]}{style_str}{msg}{reset_all_code}" for msg in message], end=end)
