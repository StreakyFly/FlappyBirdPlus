import pygame

from .image_style import render_outline, render_color_overlay


class Fonts:
    FONT_FLAPPY = 'flappy-bird.ttf'


def load_font(path: str, font_size: int) -> pygame.font:
    return pygame.font.Font(f'assets/{path}', font_size)


def flappy_text(text: str, font, text_color, outline_color, outline_width: int, shadow_distance):
    text_surface = font.render(text, True, text_color).convert_alpha()
    outlined_text_surface = render_outline(surface=text_surface,
                                           outline_color=outline_color,
                                           outline_width=outline_width,
                                           outline_algorithm=3)

    shadow_surface = render_color_overlay(surface=outlined_text_surface, color=(0, 0, 0), alpha=1)

    combined_surface = pygame.Surface((outlined_text_surface.get_width() + shadow_distance[0],
                                       outlined_text_surface.get_height() + shadow_distance[1]),
                                      pygame.SRCALPHA)
    combined_surface.blit(shadow_surface, shadow_distance)
    combined_surface.blit(outlined_text_surface, (0, 0))

    return combined_surface
