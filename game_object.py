import math
import arcade
import pymunk
from game_logic import ImpulseVector


class Bird(arcade.Sprite):
    """
    Bird class. This represents an angry bird. All the physics is handled by Pymunk,
    the init method only set some initial properties
    """
    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 12,
        max_impulse: float = 100,
        power_multiplier: float = 50,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
        scale: float = 1,
    ):
        super().__init__(image_path, scale)
        # body
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)

        impulse = min(max_impulse, impulse_vector.impulse) * power_multiplier
        self.initial_impulse = min(max_impulse, impulse_vector.impulse)
        self.power_multiplier = power_multiplier
        impulse_pymunk = impulse * pymunk.Vec2d(-1, 0)
        # apply impulse
        body.apply_impulse_at_local_point(impulse_pymunk.rotated(impulse_vector.angle))
        # shape
        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer

        space.add(body, shape)

        self.body = body
        self.shape = shape
        #boolean atributes to help us with the dynamics of the game
        self.flying = True 
        self.ability_used = False

    def update(self, delta_time):
        """
        Update the position of the bird sprite based on the physics body position
        """
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle
        if self.body.velocity.length < 5:
            self.flying = False


class Pig(arcade.Sprite):
    def __init__(
        self,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 0.4,
        collision_layer: int = 0,
    ):
        super().__init__("assets/img/pig_failed.png", 0.1)
        moment = pymunk.moment_for_circle(mass, 0, self.width / 2 - 3)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, self.width / 2 - 3)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

        # New flag to help us change levels
        self.destroyed = False

    def update(self, delta_time):
        # Sync sprite with physics body
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle
        
class PassiveObject(arcade.Sprite):
    """
    Passive object that can interact with other objects.
    """
    def __init__(
        self,
        image_path: str,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)

        moment = pymunk.moment_for_box(mass, (self.width, self.height))
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Poly.create_box(body, (self.width, self.height))
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Column(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/column.png", x, y, space)


class StaticObject(arcade.Sprite):
    def __init__(
            self,
            image_path: str,
            x: float,
            y: float,
            space: pymunk.Space,
            mass: float = 2,
            elasticity: float = 0.8,
            friction: float = 1,
            collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)




# === Additional Birds ===
class YellowBird(Bird):
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space, boost_multiplier: float = 2.0, **kwargs):
        super().__init__(image_path="assets/img/chuck.png", impulse_vector=impulse_vector, x=x, y=y, space=space, scale= 0.1,**kwargs)
        self.boost_multiplier = float(boost_multiplier)
        self._ability_used = False
        self.initial_impulse = getattr(self, "initial_impulse", impulse_vector.impulse)
        self.power_multiplier = getattr(self, "power_multiplier", 50)

    def trigger_ability(self, *args, **kwargs):
        if self._ability_used or not hasattr(self, "body"):
            return
        extra = max(0.0, (self.boost_multiplier - 1.0) * self.initial_impulse) * self.power_multiplier
        if extra > 0:
            vec = extra * pymunk.Vec2d(1, 0).rotated(self.body.angle)
            self.body.apply_impulse_at_local_point(vec)
        self._ability_used = True

class BlueBird(Bird):
    SPLIT_DEG = 30.0

    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space, **kwargs):
        super().__init__(
            image_path="assets/img/blue.png",
            impulse_vector=impulse_vector,
            x=x, y=y, space=space, scale= 0.15, **kwargs
        )
        self._ability_used = False

    def trigger_ability(self, sprites_list: arcade.SpriteList | None = None, birds_list: list | None = None):
        if self._ability_used or not hasattr(self, "body") or not hasattr(self, "shape"):
            return []

        pos = self.body.position
        speed = self.body.velocity.length
        base_angle = float(self.body.angle)

        new_birds = []
        # only spawn 2 new ones: +SPLIT_DEG and -SPLIT_DEG
        for off_deg in [self.SPLIT_DEG, -self.SPLIT_DEG]:
            ang = math.radians(off_deg) + base_angle
            iv = ImpulseVector(angle=ang, impulse=0.0)
            b = BlueBird(iv, pos.x, pos.y, self.shape.body.space)
            b.body.velocity = pymunk.Vec2d(speed, 0).rotated(ang)
            b.body.angular_velocity = self.body.angular_velocity
            new_birds.append(b)

            if sprites_list is not None:
                sprites_list.append(b)
            if birds_list is not None:
                birds_list.append(b)

        self._ability_used = True
        return new_birds


