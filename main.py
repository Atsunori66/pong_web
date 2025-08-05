# pong

import sys
import math
import pygame
import asyncio
from random import randint, choice

# Constants
WIDTH = 800
HEIGHT = 500  # Height of the play area (unchanged)
SCORE_AREA_HEIGHT = 50  # Height of the score display area
TOTAL_HEIGHT = HEIGHT + SCORE_AREA_HEIGHT  # Total height
BALL_SPEED = 12
BALL_SIZE = 20
BALL_COLOR = (255, 255, 255)
RACKET_LENGTH = int(HEIGHT / 5)
SWING = 9
AI_SWING = 5
FRAME_COLOR = (255, 255, 255)
SCORE_AREA_COLOR = (50, 50, 50)  # Dark gray


class Ball:
    """Ball class to handle ball movement and collision detection"""

    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.size = size
        self.speed = BALL_SPEED
        self.color = BALL_COLOR
        # Release a ball at random (prevents releasing at an angle of 90 and 270 degrees)
        self.direction = choice([randint(50, 70), randint(110, 130), randint(230, 250), randint(290, 310)])

    def move(self):
        """Move the ball based on its direction and speed"""
        if self.rect.centerx >= 0 and self.rect.centerx <= WIDTH:
            self.rect.centerx += int(math.cos(math.radians(self.direction)) * self.speed)
            self.rect.centery += int(math.sin(math.radians(self.direction)) * self.speed)
            return False  # No scoring event
        return True  # Ball is out of bounds, scoring event

    def reset(self):
        """Reset the ball to the center of the play area"""
        self.rect.left = int(WIDTH / 2)
        self.rect.top = int(SCORE_AREA_HEIGHT + HEIGHT / 2)  # Considering the score display area
        self.direction = choice([randint(50, 70), randint(110, 130), randint(230, 250), randint(290, 310)])
        self.speed = BALL_SPEED

    def check_collision_with_paddle(self, paddle):
        """Check collision with a paddle and update direction and speed"""
        if paddle.rect.colliderect(self.rect):
            if isinstance(paddle, PlayerPaddle):
                self.direction = -(paddle.rect.centery - self.rect.centery) + randint(-20, 20)
                self.speed += 0.3
            else:  # AI Paddle
                self.direction = 180 + (paddle.rect.centery - self.rect.centery) + randint(-20, 20)
                self.speed += 0.1
            return True
        return False

    def check_collision_with_frame(self):
        """Check collision with top and bottom frames"""
        if self.rect.centery < SCORE_AREA_HEIGHT or self.rect.centery > SCORE_AREA_HEIGHT + HEIGHT:
            self.direction = -self.direction
            self.speed += 0.2
            return True
        return False

    def draw(self, surface):
        """Draw the ball on the surface"""
        pygame.draw.ellipse(surface, self.color, self.rect)


class Paddle:
    """Base Paddle class"""

    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, surface):
        """Draw the paddle on the surface"""
        pygame.draw.rect(surface, self.color, self.rect)


class PlayerPaddle(Paddle):
    """Player controlled paddle"""

    def __init__(self):
        # Initial position considering the score display area
        x, y, width, height = 10, SCORE_AREA_HEIGHT + int((HEIGHT - RACKET_LENGTH) / 2), 10, RACKET_LENGTH
        super().__init__(x, y, width, height, (255, 255, 255))
        self.swing = SWING

    def handle_input(self, event):
        """Handle keyboard input for paddle movement"""
        if event.type == pygame.KEYDOWN:
            # Movement range considering the score display area
            if event.key == pygame.K_UP and self.rect.top > SCORE_AREA_HEIGHT + 10:
                self.rect.centery += -self.swing
            if event.key == pygame.K_DOWN and self.rect.bottom < SCORE_AREA_HEIGHT + HEIGHT - 10:
                self.rect.centery += self.swing
            # Left and right movement removed to restrict to vertical movement only


class AIPaddle(Paddle):
    """AI controlled paddle"""

    def __init__(self):
        # Initial position considering the score display area
        x, y, width, height = WIDTH - 20, SCORE_AREA_HEIGHT + int((HEIGHT - RACKET_LENGTH) / 2), 10, RACKET_LENGTH
        super().__init__(x, y, width, height, (255, 0, 0))
        self.swing = AI_SWING

    def update(self, ball):
        """Update AI paddle position based on ball position"""
        # Movement range considering the score display area
        if self.rect.centery < ball.rect.centery and self.rect.bottom < SCORE_AREA_HEIGHT + HEIGHT - 5:
            self.rect.centery += self.swing
            if self.rect.centery < ball.rect.centery - int(HEIGHT / 8) and ball.rect.centerx > int(WIDTH / 2):
                self.rect.centery += self.swing + randint(-3, 3)
        elif self.rect.centery > ball.rect.centery and self.rect.top > SCORE_AREA_HEIGHT + 5:
            self.rect.centery += -self.swing
            if self.rect.centery > ball.rect.centery + int(HEIGHT / 8) and ball.rect.centerx > int(WIDTH / 2):
                self.rect.centery += -(self.swing + randint(-3, 3))


class Score:
    """Score management class"""

    def __init__(self):
        self.player_score = 0
        self.ai_score = 0
        self.player_victory = False
        self.ai_victory = False
        self.score_font = pygame.font.Font(None, 36)
        self.end_font = pygame.font.Font(None, 50)

        # Message when a player wins
        self.message_win = self.end_font.render('You win!', True, (255, 255, 255))
        self.message_win_pos = self.message_win.get_rect()
        self.message_win_pos.centerx = int(WIDTH / 4)
        self.message_win_pos.centery = int(SCORE_AREA_HEIGHT + HEIGHT / 2)  # Considering the score display area

        # Message when a player loses
        self.message_lose = self.end_font.render('You lose...', True, (255, 255, 255))
        self.message_lose_pos = self.message_lose.get_rect()
        self.message_lose_pos.centerx = int(WIDTH * 3 / 4)
        self.message_lose_pos.centery = int(SCORE_AREA_HEIGHT + HEIGHT / 2)  # Considering the score display area

        # Deuce message
        self.deuce_text = self.score_font.render('Deuce', True, (255, 255, 255))
        self.deuce_pos = self.deuce_text.get_rect()
        self.deuce_pos.centerx = int(WIDTH / 2)
        self.deuce_pos.centery = int(SCORE_AREA_HEIGHT / 2)

        # ESC key prompt
        self.esc_text = self.score_font.render('Press ESC to exit', True, (255, 255, 255))
        self.esc_pos = self.esc_text.get_rect()
        self.esc_pos.centerx = int(WIDTH / 2)
        self.esc_pos.centery = int(SCORE_AREA_HEIGHT + HEIGHT / 2 + 50)  # Below the victory message

        # ESC key prompt box settings
        self.esc_box_padding = 10  # Padding around the text
        self.esc_box_color = (0, 0, 0)  # Black background
        self.esc_box_border_color = (255, 255, 255)  # White border

    def is_deuce(self):
        """Determine if the game is in a deuce state"""
        return ((self.player_score >= 11 or self.ai_score >= 11) and
                abs(self.player_score - self.ai_score) <= 1)

    def update(self, ball_out_of_bounds, ball):
        """Update scores based on ball position"""
        if ball_out_of_bounds:
            if (self.player_score < 11 and self.ai_score < 11) or \
               (self.player_score >= 11 and self.player_score < self.ai_score + 2) or \
               (self.ai_score >= 11 and self.ai_score < self.player_score + 2):
                if ball.rect.centerx > WIDTH:
                    self.player_score += 1
                    ball.reset()
                if ball.rect.centerx < 0:
                    self.ai_score += 1
                    ball.reset()

            # Check for victory conditions
            if self.player_score >= 11 and self.player_score >= self.ai_score + 2:
                self.player_victory = True
            if self.ai_score >= 11 and self.ai_score >= self.player_score + 2:
                self.ai_victory = True

    def draw(self, surface):
        """Draw scores and victory messages"""
        # Player score
        player_score_text = self.score_font.render('You: ' + str(self.player_score), True, (255, 255, 255))
        player_score_pos = player_score_text.get_rect()
        player_score_pos.centerx = int(WIDTH / 4)
        player_score_pos.centery = int(SCORE_AREA_HEIGHT / 2)  # Centered position

        # AI score
        ai_score_text = self.score_font.render('Pong AI: ' + str(self.ai_score), True, (255, 255, 255))
        ai_score_pos = ai_score_text.get_rect()
        ai_score_pos.centerx = int(WIDTH * 3 / 4)
        ai_score_pos.centery = int(SCORE_AREA_HEIGHT / 2)  # Centered position

        # Draw scores
        surface.blit(player_score_text, player_score_pos)
        surface.blit(ai_score_text, ai_score_pos)

        # Draw deuce message if applicable
        if self.is_deuce():
            surface.blit(self.deuce_text, self.deuce_pos)

        # Draw victory messages if applicable
        if self.player_victory:
            surface.blit(self.message_win, self.message_win_pos)
            # Draw background box for ESC key prompt message
            esc_box = pygame.Rect(
                self.esc_pos.left - self.esc_box_padding,
                self.esc_pos.top - self.esc_box_padding,
                self.esc_pos.width + (self.esc_box_padding * 2),
                self.esc_pos.height + (self.esc_box_padding * 2)
            )
            pygame.draw.rect(surface, self.esc_box_color, esc_box)
            pygame.draw.rect(surface, self.esc_box_border_color, esc_box, 2)  # Draw border (2 pixels thick)
            surface.blit(self.esc_text, self.esc_pos)  # ESC key prompt message
        if self.ai_victory:
            surface.blit(self.message_lose, self.message_lose_pos)
            # Draw background box for ESC key prompt message
            esc_box = pygame.Rect(
                self.esc_pos.left - self.esc_box_padding,
                self.esc_pos.top - self.esc_box_padding,
                self.esc_pos.width + (self.esc_box_padding * 2),
                self.esc_pos.height + (self.esc_box_padding * 2)
            )
            pygame.draw.rect(surface, self.esc_box_color, esc_box)
            pygame.draw.rect(surface, self.esc_box_border_color, esc_box, 2)  # Draw border (2 pixels thick)
            surface.blit(self.esc_text, self.esc_pos)  # ESC key prompt message


class Renderer:
    """Rendering class to handle all drawing operations"""

    def __init__(self, surface):
        self.surface = surface

        # Create frame rectangles (adjusted for score area)
        self.frame_top = pygame.Rect(0, SCORE_AREA_HEIGHT, WIDTH, 5)
        self.frame_bottom = pygame.Rect(0, SCORE_AREA_HEIGHT + HEIGHT - 5, WIDTH, 5)
        self.frame_center = pygame.Rect(int(WIDTH / 2 - 2), SCORE_AREA_HEIGHT, 4, HEIGHT)
        self.frame_left = pygame.Rect(0, SCORE_AREA_HEIGHT, 5, HEIGHT)
        self.frame_right = pygame.Rect(WIDTH - 5, SCORE_AREA_HEIGHT, 5, HEIGHT)

        # Score area and divider
        self.score_area = pygame.Rect(0, 0, WIDTH, SCORE_AREA_HEIGHT)
        self.score_divider = pygame.Rect(0, SCORE_AREA_HEIGHT - 2, WIDTH, 2)

    def clear(self):
        """Clear the screen with background colors"""
        # Fill play area with royal blue
        self.surface.fill('royalblue2', pygame.Rect(0, SCORE_AREA_HEIGHT, WIDTH, HEIGHT))
        # Fill score area with dark blue
        self.surface.fill(SCORE_AREA_COLOR, self.score_area)

    def draw_frames(self):
        """Draw the game frames and score area divider"""
        # Draw score area divider
        pygame.draw.rect(self.surface, FRAME_COLOR, self.score_divider)

        # Draw game frames
        pygame.draw.rect(self.surface, FRAME_COLOR, self.frame_top)
        pygame.draw.rect(self.surface, FRAME_COLOR, self.frame_bottom)
        pygame.draw.rect(self.surface, FRAME_COLOR, self.frame_center)
        pygame.draw.rect(self.surface, FRAME_COLOR, self.frame_left)
        pygame.draw.rect(self.surface, FRAME_COLOR, self.frame_right)

    def draw_game_objects(self, ball, player_paddle, ai_paddle, score):
        """Draw all game objects"""
        self.clear()
        self.draw_frames()
        score.draw(self.surface)
        player_paddle.draw(self.surface)
        ai_paddle.draw(self.surface)
        ball.draw(self.surface)
        pygame.display.update()


class Game:
    """Main game class to manage the game loop and objects"""

    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.key.set_repeat(1, 6)
        self.clock = pygame.time.Clock()
        self.surface = pygame.display.set_mode((WIDTH, TOTAL_HEIGHT))
        pygame.display.set_caption('Pong')

        # Create game objects
        self.ball = Ball(self.surface.get_rect().centerx, SCORE_AREA_HEIGHT + HEIGHT / 2, BALL_SIZE)
        self.player_paddle = PlayerPaddle()
        self.ai_paddle = AIPaddle()
        self.score = Score()
        self.renderer = Renderer(self.surface)

        # Game state
        self.running = True
        self.game_over = False  # Game over flag

    def handle_events(self):
        """Handle game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # Disable paddle control when game is over
                if not self.game_over:
                    self.player_paddle.handle_input(event)

    def update(self):
        """Update game state"""
        # Set game over flag when victory/defeat occurs
        if self.score.player_victory or self.score.ai_victory:
            self.game_over = True

        # Do not update when game is over
        if self.game_over:
            return

        # Update AI paddle
        self.ai_paddle.update(self.ball)

        # Check collisions
        self.ball.check_collision_with_paddle(self.player_paddle)
        self.ball.check_collision_with_paddle(self.ai_paddle)
        self.ball.check_collision_with_frame()

        # Move ball and check for scoring
        ball_out_of_bounds = self.ball.move()
        self.score.update(ball_out_of_bounds, self.ball)

    def render(self):
        """Render the game"""
        self.renderer.draw_game_objects(self.ball, self.player_paddle, self.ai_paddle, self.score)

    # run()はasyncio対応のため未使用



async def main():
    """Main function to start the game (pygbag/asyncio compatible)"""
    game = Game()
    try:
        while game.running:
            game.handle_events()
            game.update()
            game.render()
            await asyncio.sleep(0)  # Yield control to event loop
    except Exception as e:
        # ブラウザやpygbag環境での例外を握りつぶす
        pass
    finally:
        try:
            pygame.quit()
        except Exception:
            pass
        try:
            sys.exit()
        except Exception:
            pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except SystemExit:
        pass
