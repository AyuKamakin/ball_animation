import pygame
import sys
import math
import random

# Константы
GRAVITY = 0.01
DAMPING_COEFFICIENT = 1
BALL_RADIUS = 10
BOUNDARY_RADIUS = 200
SIZE_WIDTH = int(1600 * 0.7)
SIZE_HEIGHT = int(900 * 0.7)
MAX_BALLS = 4000
INITIAL_BALLS_COUNT = 5  # Начальное количество шариков
NEW_BALLS_ON_COLLISION = 1  # Количество новых шариков при столкновении

INITIAL_SPEED_RANGE = 20
INITIAL_SPEED_X_RANGE = INITIAL_SPEED_RANGE  # Максимальная скорость по оси X
INITIAL_SPEED_Y_RANGE = INITIAL_SPEED_RANGE  # Максимальная скорость по оси Y

# Константы для малого круга
SMALL_CIRCLE_RADIUS = 30
SMALL_CIRCLE_COLOR = (0, 0, 255)  # Синий цвет
NUM_SMALL_CIRCLES = 4  # Количество малых кругов
POLYGON_SIDE_LENGTH = 250  # Длина стороны правильного многоугольника
ROTATION_SPEED = 0.001  # Скорость вращения в радианах за кадр
INITIAL_ROTATION_STEP_DEGREES = 0  # Начальный шаг поворота в градусах

# Инициализация Pygame
pygame.init()


# Функция для преобразования градусов в радианы
def degrees_to_radians(degrees):
    return degrees * (math.pi / 180)


# Преобразование начального шага поворота в радианы
INITIAL_ROTATION_STEP = degrees_to_radians(INITIAL_ROTATION_STEP_DEGREES)


class Ball:
    def __init__(self, color, radius, position, speed):
        self.color = color
        self.radius = radius
        self.position = position
        self.speed = speed

    def update(self, gravity):
        self.speed[1] += gravity
        self.position[0] += self.speed[0]
        self.position[1] += self.speed[1]

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, [int(self.position[0]), int(self.position[1])], self.radius)

    def handle_collision(self, center, border_radius, damping):
        dx = self.position[0] - center[0]
        dy = self.position[1] - center[1]

        # Проверка на превышение пределов
        if abs(dx) > 1e6 or abs(dy) > 1e6:
            print(f"Position out of bounds: ({self.position[0]}, {self.position[1]})")
            self.position = [center[0], center[1]]
            self.speed = [0, 0]

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance + self.radius >= border_radius:
            norm_dx = dx / distance
            norm_dy = dy / distance

            self.position[0] = center[0] + norm_dx * (border_radius - self.radius)
            self.position[1] = center[1] + norm_dy * (border_radius - self.radius)

            speed_dot_norm = self.speed[0] * norm_dx + self.speed[1] * norm_dy
            self.speed[0] -= 2 * speed_dot_norm * norm_dx
            self.speed[1] -= 2 * speed_dot_norm * norm_dy

            self.speed[0] *= damping
            self.speed[1] *= damping

            return True

        return False


class CircularBoundary:
    def __init__(self, color, radius, center):
        self.color = color
        self.radius = radius
        self.center = center

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.center, self.radius, 1)


class SmallCircle:
    def __init__(self, color, radius, position):
        self.color = color
        self.radius = radius
        self.position = position

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    def check_collision(self, ball):
        dx = ball.position[0] - self.position[0]
        dy = ball.position[1] - self.position[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        return distance <= self.radius + ball.radius


class SmallCircleGroup:
    def __init__(self, num_circles, side_length, center, rotation_speed, initial_rotation_step):
        self.num_circles = num_circles
        self.side_length = side_length
        self.center = center
        self.rotation_speed = rotation_speed
        self.current_angle = initial_rotation_step
        self.small_circles = self.create_circles()

    def create_circles(self):
        circles = []
        angle = 2 * math.pi / self.num_circles
        radius = self.side_length / (2 * math.sin(math.pi / self.num_circles))
        for i in range(self.num_circles):
            x = self.center[0] + radius * math.cos(i * angle + self.current_angle)
            y = self.center[1] + radius * math.sin(i * angle + self.current_angle)
            circles.append(SmallCircle(SMALL_CIRCLE_COLOR, SMALL_CIRCLE_RADIUS, (x, y)))
        return circles

    def update(self):
        self.current_angle += self.rotation_speed
        self.small_circles = self.create_circles()

    def draw(self, screen):
        for circle in self.small_circles:
            circle.draw(screen)

    def check_collision(self, ball):
        return any(circle.check_collision(ball) for circle in self.small_circles)


class Game:
    def __init__(self):
        self.size = self.width, self.height = SIZE_WIDTH, SIZE_HEIGHT
        self.screen = pygame.display.set_mode(self.size)
        self.black = (0, 0, 0)

        self.border = CircularBoundary(color=(0, 255, 0), radius=BOUNDARY_RADIUS,
                                       center=(self.width // 2, self.height // 2))
        self.small_circle_group = SmallCircleGroup(NUM_SMALL_CIRCLES, POLYGON_SIDE_LENGTH,
                                                   (self.width // 2, self.height // 2), ROTATION_SPEED,
                                                   INITIAL_ROTATION_STEP)

        self.balls = []
        for _ in range(INITIAL_BALLS_COUNT):
            initial_speed = [random.uniform(-INITIAL_SPEED_X_RANGE, INITIAL_SPEED_X_RANGE),
                             random.uniform(-INITIAL_SPEED_Y_RANGE, INITIAL_SPEED_Y_RANGE)]
            initial_ball = Ball(color=self.random_color(), radius=BALL_RADIUS,
                                position=[self.border.center[0], self.border.center[1]], speed=initial_speed)
            self.balls.append(initial_ball)

        self.gravity = GRAVITY
        self.damping = DAMPING_COEFFICIENT

        self.font = pygame.font.Font(None, 36)  # Шрифт для отображения текста

    def random_color(self):
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def random_speed_variation(self, speed):
        variation = [random.uniform(-0.05, 0.05) * s for s in speed]
        return [s + v for s, v in zip(speed, variation)]

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            pygame.time.delay(10)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def update(self):
        new_balls = []
        self.balls = [ball for ball in self.balls if not self.small_circle_group.check_collision(ball)]
        for ball in self.balls:
            ball.update(self.gravity)
            collision_occurred = ball.handle_collision(self.border.center, self.border.radius, self.damping)
            if collision_occurred and len(self.balls) + len(new_balls) < MAX_BALLS:
                for _ in range(NEW_BALLS_ON_COLLISION):
                    new_speed = self.random_speed_variation(ball.speed)
                    new_ball = Ball(self.random_color(), ball.radius, ball.position[:], new_speed)
                    new_balls.append(new_ball)
        self.balls.extend(new_balls)
        self.small_circle_group.update()

    def draw(self):
        self.screen.fill(self.black)
        self.border.draw(self.screen)
        self.small_circle_group.draw(self.screen)
        for ball in self.balls:
            ball.draw(self.screen)
        self.draw_ball_count()
        pygame.display.flip()

    def draw_ball_count(self):
        ball_count_text = self.font.render(f'Balls: {len(self.balls)}', True, (255, 255, 255))
        self.screen.blit(ball_count_text, (10, 10))


if __name__ == "__main__":
    game = Game()
    game.run()
