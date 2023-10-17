import pygame


class Fonts:
    FONT_FLAPPY = 'flappy-bird.ttf'


def load_font(path: str, font_size: int) -> pygame.font:
    return pygame.font.Font(f'assets/{path}', font_size)


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


def _squarepoints_corners_chonk(r):
    """
    i am really good at naming functions
    """
    points = set()
    points.add((r, r))
    points.add((r, -r))
    points.add((-r, r))
    points.add((-r, -r))

    return list(points)


def render_outline(text, font, text_color, outline_color, outline_width):
    """
    Add outline to the text.
    """
    text_surface = font.render(text, True, text_color).convert_alpha()
    w = text_surface.get_width() + 2 * outline_width
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * outline_width), pygame.SRCALPHA)
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, outline_color).convert_alpha(), (0, 0))

    for dx, dy in _squarepoints_corners_chonk(outline_width):
        surf.blit(osurf, (dx + outline_width, dy + outline_width))

    surf.blit(text_surface, (outline_width, outline_width))

    return surf


def render_color_overlay(surface, color=(0, 0, 0), alpha: float = 1):
    """
    Color the surface with a solid color.
    """
    surface_mask = pygame.mask.from_surface(surface)
    colored_mask = surface_mask.to_surface(unsetcolor=(0, 0, 0, 0),
                                           setcolor=(color[0], color[1], color[2], int(255 * alpha)))

    return colored_mask


def flappy_font(text: str, font, text_color, stroke_color, stroke_width: int, shadow_distance):
    outlined_text_surface = render_outline(
        text=text, font=font, text_color=text_color,
        outline_color=stroke_color, outline_width=stroke_width)

    shadow_surface = render_color_overlay(surface=outlined_text_surface, color=(0, 0, 0), alpha=1)

    combined_surface = pygame.Surface((outlined_text_surface.get_width() + shadow_distance[0],
                                       outlined_text_surface.get_height() + shadow_distance[1]),
                                      pygame.SRCALPHA)
    combined_surface.blit(shadow_surface, shadow_distance)
    combined_surface.blit(outlined_text_surface, (0, 0))

    return combined_surface
