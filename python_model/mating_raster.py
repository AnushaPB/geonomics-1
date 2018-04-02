class MatingRaster:
    def __init__(self, params):
        self.dims = params['dims']
        self.mating_radius = params['mating_radius']
        self.grid_size = 2 * self.mating_radius

        self.x = self.dims[0] / self.grid_size
        self.y = self.dims[0] / self.grid_size

        self.offset1 = [[set() for _ in range(int(self.x) + 1)] for j in range(int(self.y) + 1)]
        self.offset2 = [[set() for _ in range(int(self.x) + 1)] for j in range(int(self.y) + 1)]

    def add(self, ind):
        self.__add(ind.x, ind.y, ind)

    def remove(self, ind):
        self.__remove(ind.x, ind.y, ind)
        return None

    def move(self, old_pos, new_pos, ind):
        self.__remove(old_pos[0], old_pos[1], ind)
        self.__add(new_pos[0], new_pos[1], ind)
        return None

    #########################
    # Private Methods Below #
    #########################

    def __get_set(self, x_pos, y_pos):
        # TODO: notimplemented
        set1 = self.offset1[int(x_pos)][int(y_pos)]
        set2 = self.offset1[int(x_pos + self.mating_radius)][int(y_pos + self.mating_radius)]
        return set1, set2

    def __add(self, x_pos, y_pos, ind):
        # private method
        set1, set2 = self.__get_set(x_pos, y_pos)
        set1.add(ind)
        set2.add(ind)
        return None

    def __remove(self, x_pos, y_pos, ind):
        # private method
        set1, set2 = self.__get_set(x_pos, y_pos)
        set1.remove(ind)
        set2.remove(ind)
        return None
