import pygame


def render_color_overlay(surface, color=(0, 0, 0), alpha: float = 1):
    """
    Color the surface with a solid color.
    """
    surface_mask = pygame.mask.from_surface(surface)
    colored_mask = surface_mask.to_surface(unsetcolor=(0, 0, 0, 0),
                                           setcolor=(color[0], color[1], color[2], int(255 * alpha)))

    return colored_mask


def render_outline(surface: pygame.Surface, outline_color, outline_width, outline_algorithm: int):
    """
    Add outline to the surface.
    """
    w = surface.get_width() + 2 * outline_width
    h = surface.get_height()

    osurf = pygame.Surface((w, h + 2 * outline_width), pygame.SRCALPHA)
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(render_color_overlay(surface, color=outline_color), (0, 0))

    for dx, dy in get_points(outline_algorithm, outline_width):
        surf.blit(osurf, (dx + outline_width, dy + outline_width))

    surf.blit(surface, (outline_width, outline_width))

    return surf


def get_points(outline_algorithm: int, outline_width: int):
    match outline_algorithm:
        case 0:
            points = _circlepoints(outline_width)
        case 1:
            points = _squarepoints(outline_width)
        case 2:
            points = _squarepoints_corners(outline_width)
        case 3:
            points = _squarepoints_corners_for_chonkers(outline_width)
        case 4:
            points = _squarepoints_corners_for_less_chonkers(outline_width)
        case _:
            raise ValueError("Invalid argument for outline_algorithm.")

    return points


def _circlepoints(r):
    r = int(round(r))
    x, y, e = r, 0, 1 - r
    points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()

    return points


def _squarepoints(r):
    points = set()
    for i in range(0, r+1):
        points.add((0, i))
        points.add((0, -i))
        points.add((i, 0))
        points.add((-i, 0))

    return list(points)


def _squarepoints_corners(r):
    points = set()
    for i in range(0, r+1):
        points.add((i, i))
        points.add((i, -i))
        points.add((-i, i))
        points.add((-i, -i))

    return list(points)


def _squarepoints_corners_for_chonkers(r):
    points = set()
    points.add((r, r))
    points.add((r, -r))
    points.add((-r, r))
    points.add((-r, -r))

    return list(points)

def _squarepoints_corners_for_less_chonkers(r):
    """
    I am really good at naming functions.
    """
    points = set()
    points.add((r, r))
    points.add((r, -r))
    points.add((-r, r))
    points.add((-r, -r))
    points.add((0, r))
    points.add((0, -r))
    points.add((r, 0))
    points.add((-r, 0))

    return list(points)
