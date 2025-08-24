import logging
import arcade
import pymunk
import time

from game_object import Bird, Column, Pig, YellowBird, BlueBird
from game_logic import get_impulse_vector, Point2D, get_distance

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

WIDTH = 1500
HEIGHT = 800
TITLE = "Angry birds"
GRAVITY = -900
GROUND_Y = 50  
SLING_X = 200
SLING_Y = GROUND_Y + 1  # a little above the ground
SLING_RADIUS = 100        # max pull distance


class App(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("assets/img/background3.png")
        self.sling_texture = arcade.load_texture("assets/img/sling-3.png")
        # creating pymunk space
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)

        # floor
        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.friction = 10
        self.space.add(floor_body, floor_shape)
        
        #walls
        static_body = self.space.static_body
        height = HEIGHT  
        width = WIDTH    

        # Left wall
        left_wall = pymunk.Segment(static_body, (0, 0), (0, height), 1)
        left_wall.elasticity = 0.8
        left_wall.friction = 1.0

        # Right wall
        right_wall = pymunk.Segment(static_body, (width, 0), (width, height), 1)
        right_wall.elasticity = 0.2
        right_wall.friction = 1.0

        # Add to space
        self.space.add(left_wall, right_wall)

        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()

        self.start_point = Point2D(0, 0)
        self.end_point = Point2D(0, 0)
        self.distance = 0
        self.draw_line = False

        # collision handler
        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler
        
        self.selected_bird = None 
        self.current_bird = None
        
        
        # Game state
        self.current_level = 1
        self.max_levels = 3
        self.score = 0

        # Sprite lists
        self.pigs = []
        self.columns = []
        self.birds = []

        # Load first level
        self.load_level(self.current_level)
        
        #text
        self.score_text = arcade.Text(f"Score: {self.score}", 20, HEIGHT-40, arcade.color.WHITE, 24)
        self.level_text = arcade.Text(f"Level: {self.current_level}", WIDTH-150, HEIGHT-40, arcade.color.WHITE, 24)


    def collision_handler(self, arbiter, space, data):
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < 100:
            return True
        logger.debug(impulse_norm)
        if impulse_norm > 1200:
            for obj in self.world:
                if obj.shape in arbiter.shapes:
                    if isinstance(obj, Pig) and not obj.destroyed:
                        obj.destroyed = True
                        self.score += 1  # <-- adding point for pig
                        self.score_text.text = f"Score: {self.score}"
                    obj.remove_from_sprite_lists()
                    self.space.remove(obj.shape, obj.body)


    def add_columns(self):
        for x in range(WIDTH // 2, WIDTH, 400):
            column = Column(x, 50, self.space)
            self.sprites.append(column)
            self.world.append(column)

    def add_pigs(self):
        pig1 = Pig(WIDTH / 2, 100, self.space)
        self.sprites.append(pig1)
        self.world.append(pig1)

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)  # updating physics simulations
        self.sprites.update(delta_time)
        
        for bird in self.birds[:]:
        # Check if bird touched the floor (y <= ground level, e.g. 50)
            if bird.center_y <= 50:  
                if not hasattr(bird, "landed_time"):
                    bird.landed_time = time.time()  # start countdown
                    print(f"{type(bird).__name__} landed!")
                else:
                    if bird.landed_time is not None and time.time() - bird.landed_time >= 5:  # 5 sec delay
                        bird.remove_from_sprite_lists()
                        if hasattr(bird, "body") and hasattr(bird, "shape"):
                            self.space.remove(bird.shape, bird.body)
                        self.birds.remove(bird)
                                
        # checking if all pigs are destroyed
        if all(getattr(pig, "destroyed", False) for pig in self.pigs):
            # Bonus score for remaining birds
            self.score += len(self.birds) * 50

            self.current_level += 1
            if self.current_level <= self.max_levels:
                self.load_level(self.current_level)
                print(f"Level {self.current_level} loaded!")
            else:
                # switching to end screen
                end_view = EndScreen(self.score)
                self.window.show_view(end_view)

            
            self.score_text.text = f"Score: {self.score}"
            self.level_text.text = f"Level: {self.current_level}"    

            
    
    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.KEY_1:
            self.selected_bird = 1
        elif symbol == arcade.key.KEY_2:
            self.selected_bird = 2
        elif symbol == arcade.key.KEY_3:
            self.selected_bird = 3
        # space key to trigger the ability form birds      
        elif symbol == arcade.key.SPACE and self.current_bird and getattr(self.current_bird, "flying", False):
            if hasattr(self.current_bird, 'trigger_ability'):
                self.current_bird.trigger_ability(self.sprites, self.birds)
                self.is_triggering_ability = False


    def on_mouse_press(self, x, y, button, modifiers):
            self.start_point = Point2D(x, y)
            self.end_point = Point2D(x, y)
            self.draw_line = True
            logger.debug(f"Start Point: {self.start_point}")


    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            self.end_point = Point2D(x, y)
            logger.debug(f"Dragging to: {self.end_point}")

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            logger.debug(f"Releasing from: {self.end_point}")
            self.draw_line = False
            impulse_vector = get_impulse_vector(self.end_point, self.start_point)
            if self.selected_bird == 1:
                bird = Bird("assets/img/red-bird3.png", impulse_vector, x, y, self.space)
            elif self.selected_bird == 2:
                bird = YellowBird(impulse_vector, x, y, self.space)
            elif self.selected_bird == 3:
                bird = BlueBird(impulse_vector, x, y, self.space) 
            else:
                bird = Bird("assets/img/red-bird3.png", impulse_vector, x, y, self.space)
            self.sprites.append(bird)
            self.birds.append(bird)
            self.current_bird = bird


    def on_draw(self):
        self.clear()
        #drawing background
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))
        # drawing slingshot
        arcade.draw_texture_rect(self.sling_texture, arcade.LRBT(SLING_X, SLING_Y, 20, 150))
        self.score_text.draw()
        self.level_text.draw()
        self.sprites.draw()
        if self.draw_line:
            arcade.draw_line(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y, arcade.color.BLACK, 3)

    #level handler
    def load_level(self, level_number: int):
    # Clear previous level objects
        self.clear_level()

        if level_number == 1:
            base_x_positions = [700, 800, 900]  
            column_height = 100  
            pig_offset_y = 1   

            for x in base_x_positions:
                col = Column(x, GROUND_Y + column_height / 2, self.space)
                self.columns.append(col)

                pig_y = GROUND_Y + column_height + pig_offset_y
                pig = Pig(x, pig_y, self.space)
                self.pigs.append(pig)

        elif level_number == 2:
            positions = [
                (750, 100), 
                (850, 100),
                (950, 100), 
                (1050, 100),
                (1150, 100)
            ]
            pig_offset_y = 1
            for x, col_y in positions:
                col = Column(x, col_y, self.space)
                self.columns.append(col)

                pig_y = col_y + 50 + pig_offset_y
                pig = Pig(x, pig_y, self.space)
                self.pigs.append(pig)

        elif level_number == 3:
            column_height = 120
            pig_offset_y = 1
            base_x_left = 650
            
            for i in range(2):
                col_y = GROUND_Y + i * column_height
                col = Column(base_x_left, col_y, self.space)
                self.columns.append(col)
            
            positions = [
                (750, 100), 
                (850, 100),
                (950, 100), 
                (1050, 100),
                (1150, 100)
            ]
            
            for x, col_y in positions:
                col = Column(x, col_y, self.space)
                self.columns.append(col)

                pig_y = col_y + 50 + pig_offset_y
                pig = Pig(x, pig_y, self.space)
                self.pigs.append(pig)

            base_x_right = 1250
            for i in range(2):
                col_y = GROUND_Y + i * column_height
                col = Column(base_x_right, col_y, self.space)
                self.columns.append(col)

        # adding all objects to sprites and world lists
        for col in self.columns:
            self.sprites.append(col)
            self.world.append(col)
        for pig in self.pigs:
            self.sprites.append(pig)
            self.world.append(pig)


                                
    def clear_level(self):
        for sprite in self.sprites:
            # remove physics bodies if they exist
            if hasattr(sprite, "shape") and hasattr(sprite, "body"):
                self.space.remove(sprite.shape, sprite.body)
            sprite.remove_from_sprite_lists()
        self.sprites = arcade.SpriteList()
        self.birds = []
        self.pigs = []
        self.columns = []
        self.world = arcade.SpriteList() 
        
        
import arcade


class BeginScreen(arcade.View):
    def __init__(self):
        super().__init__()
        #loading the background, text and play images
        self.background = arcade.load_texture("assets/img/background3.png")
        self.play_button_texture = arcade.load_texture("assets/img/play-button.png")
        self.logo_texture = arcade.load_texture("assets/img/text.png")

        self.button_width = 200
        self.button_height = 100
        self.button_center_x = self.window.width // 2
        self.button_center_y = self.window.height // 2 - 100

    def on_draw(self):
        self.clear()
        
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, self.window.width, 0, self.window.height))

        arcade.draw_texture_rect(
            texture=self.logo_texture,
            rect=arcade.LRBT(
                left=self.window.width / 2 - self.logo_texture.width / 2,
                right=self.window.width / 2 + self.logo_texture.width / 2,
                bottom=self.window.height / 2,
                top=self.window.height / 2 + self.logo_texture.height
            )
        )

        arcade.draw_texture_rect(
            texture=self.play_button_texture,
            rect=arcade.LRBT(
                left=self.button_center_x - self.button_width / 2,
                right=self.button_center_x + self.button_width / 2,
                bottom=self.button_center_y - self.button_height / 2,
                top=self.button_center_y + self.button_height / 2
            )
        )

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # checking if click is inside the Play button image bounds
            if (self.button_center_x - self.button_width / 2 <= x <= self.button_center_x + self.button_width / 2
                and self.button_center_y - self.button_height / 2 <= y <= self.button_center_y + self.button_height / 2
            ):
                print("Play clicked!") 
                game_view = App()
                self.window.show_view(game_view)





class EndScreen(arcade.View):
    def __init__(self,score):
        super().__init__()
        self.score = score
        self.game_over_texture = arcade.load_texture("assets/img/game-over.png") 

    def on_draw(self):
        self.clear()
                
        arcade.draw_texture_rect(
            texture=self.game_over_texture,
            rect=arcade.LRBT(
                left=self.window.width / 2 - self.game_over_texture.width / 2,
                right=self.window.width / 2 + self.game_over_texture.width / 2,
                bottom=self.window.height / 2 - self.game_over_texture.height / 2 + 50,
                top=self.window.height / 2 + self.game_over_texture.height / 2 + 50
            )
        )
        
        arcade.draw_text(
            f"Final Score: {self.score}",
            x=self.window.width / 2,
            y=self.window.height / 2 - 50,  
            color=arcade.color.WHITE,
            font_size=24,
            anchor_x="center"
        )
        
    def on_mouse_press(self, x, y, button, modifiers):
        # Only restart if left mouse button clicked
        if button == arcade.MOUSE_BUTTON_LEFT:
            print("Mouse pressed on EndScreen")  
            new_game = App()
            self.window.show_view(new_game)



def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = BeginScreen()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()
    
