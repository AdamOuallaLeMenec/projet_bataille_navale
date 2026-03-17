import pygame


def draw_centered_text(text, font, y, color=(0, 0, 0), window_surface=None):
    surface = font.render(text, True, color)
    window_surface.blit(surface, surface.get_rect(center=(1180 // 2, y)))


def draw_lines(window_surface):
    DARK_GREY = (41, 41, 46)
    pygame.draw.line(window_surface, DARK_GREY, (10, 10), (1170, 10), 3)
    pygame.draw.line(window_surface, DARK_GREY, (1170, 10), (1170, 690), 3)
    pygame.draw.line(window_surface, DARK_GREY, (1170, 690), (10, 690), 3)
    pygame.draw.line(window_surface, DARK_GREY, (10, 10), (10, 690), 3)
    pygame.draw.line(window_surface, DARK_GREY, (10, 600), (1170, 600), 3)

####################################
def display_instruction(text, color, window_surface, body_font):
    DARK_GREY = (41, 41, 46)
    panel = pygame.Rect(25, 612, 1130, 65)
    pygame.draw.rect(window_surface, DARK_GREY, panel, border_radius=8)
    label = body_font.render(text, True, color)
    window_surface.blit(label, label.get_rect(center=panel.center))
