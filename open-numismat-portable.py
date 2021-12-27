#!/usr/bin/env python3
#
# This file is part of OpenNumismat (http://opennumismat.github.io/).
#
# OpenNumismat is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# OpenNumismat is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenNumismat; If not, see <http://www.gnu.org/licenses/>.

from OpenNumismat import version

version.Portable = True

if __name__ == "__main__":
    from OpenNumismat.pathes import init_pathes
    init_pathes()

    from OpenNumismat.main import main
    main()
