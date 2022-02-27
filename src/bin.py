 # For every object in the scene, do physics magic
            ball = self.scene["ball"]
            for object in self.scene.values():
                if object == ball or object == self.scene["slider2"]:
                    continue

                # Convert ball position to object space
                ortho = Transform2D(
                    object.transform.position(),
                    object.transform.right() / np.linalg.norm(object.transform.right()),
                    object.transform.up() / np.linalg.norm(object.transform.up())
                )

                object_origin = object.transform.components[2]
                ball_velocity = np.array((ball.velocity[0], ball.velocity[1], 0))

                ray_origin = ball.transform.components[2]
                ray_direction = ball_velocity / np.linalg.norm(ball_velocity)

                local_origin = ortho.components.dot(ray_origin - object_origin)
                local_direction = ortho.components.dot(ray_direction)

                boundary_min = -0.5 * object.transform.size()
                boundary_max = 0.5 * object.transform.size()
  
                near, far = raycastBox(local_origin, local_direction, boundary_min, boundary_max)

                if ((near > 0) and (near < far)):
                    hit = ray_origin + near * ray_direction

                    self.scene["collision"].transform = Transform2D(hit[0:2], (100, 0), (0, 100))
