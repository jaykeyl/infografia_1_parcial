# Justificación: Uso de `hasattr` / `getattr` vs `try/except`

En Python existen varias formas de manejar atributos que **pueden no existir** en un objeto.  
Dos enfoques comunes son:

- Usar **`hasattr` / `getattr`**, que permiten escribir código más claro y legible.
- Usar **`try/except`**, que también funciona, pero suele ser más largo y menos expresivo.

A continuación, se muestran casos de este proyecto donde se comparan ambas formas.


## Caso 1 — Pájaro tocando el piso

### Versión con `hasattr`

```python
if not hasattr(bird, "landed_time"):
    bird.landed_time = time.time()
else:
    if bird.landed_time is not None and time.time() - bird.landed_time >= 5:
        bird.remove_from_sprite_lists()
        if hasattr(bird, "body") and hasattr(bird, "shape"):
            self.space.remove(bird.shape, bird.body)
```
### Versión con `try/except`

```python
try:
    if bird.landed_time is None:
        bird.landed_time = time.time()
    elif time.time() - bird.landed_time >= 5:
        bird.remove_from_sprite_lists()
        try:
            self.space.remove(bird.shape, bird.body)
        except AttributeError:
            pass
except AttributeError:
    bird.landed_time = time.time()
```

## Caso 2 — Revisar si todos los cerditos están destruidos

### Versión con getattr 
```python
if all(getattr(pig, "destroyed", False) for pig in self.pigs):
    self.current_level += 1
    self.load_level(self.current_level)
```

### Versión con try/except
```python
all_destroyed = True
for pig in self.pigs:
    try:
        if not pig.destroyed:
            all_destroyed = False
            break
    except AttributeError:
        all_destroyed = False
        break

if all_destroyed:
    self.current_level += 1
    self.load_level(self.current_level)
```

El uso de `hasattr` o `getattr` se hizo con la intencion de tener flexibilidad con distintos objetos usados en el juego, es decir, para hacerlo torelante a los distintos tipos de sprite.
Otra cualidad que tienen estas funciones es que ayuda mucho más a la legibilidad y la comprensión de código para personas externas al proyecto.
Además tener estas funciones ayudan a la escalabilidad del proyecto en un futuro.
