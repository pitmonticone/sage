r"""
Fast Rank Two Crystals
"""
#*****************************************************************************
#       Copyright (C) 2007 Anne Schilling <anne at math.ucdavis.edu>
#                          Nicolas Thiery <nthiery at users.sf.net>
#                          Ben Brubaker   <brubaker at math.mit.edu>
#                          Daniel Bump    <bump at match.stanford.edu>
#                          Justin Walker  <justin at mac.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#  The full text of the GPL is available at:
#
#                  http://www.gnu.org/licenses/
#****************************************************************************

from sage.structure.unique_representation import UniqueRepresentation
from sage.structure.parent import Parent
from sage.categories.classical_crystals import ClassicalCrystals
from sage.structure.element import Element, parent
from sage.combinat.root_system.cartan_type import CartanType


class FastCrystal(UniqueRepresentation, Parent):
    """
    An alternative implementation of rank 2 crystals. The root
    operators are implemented in memory by table lookup. This means
    that in comparison with the CrystalsOfTableaux, these crystals
    are slow to instantiate but faster for computation. Implemented for
    types A2, B2 and C2.

    Input: CartanType and a shape. The CartanType is ['A',2], ['B',2]
    or ['C',2]. The shape is of the form [l1,l2] where l1 and l2 are
    either integers or (in type B) half integers such that l1-l2 is
    integral. It is assumed that l1 >= l2 >= 0. If l1 and l2 are
    integers, this will produce the a crystal isomorphic to the one
    obtained by CrystalOfTableaux(type, shape=[l1,l2]). Furthermore
    FastCrystal(['B', 2], l1+1/2, l2+1/2) produces a crystal isomorphic
    to the following crystal T::

        C = CrystalOfTableaux(['B',2], shape=[l1,l2])
        D = CrystalOfSpins(['B',2])
        T = TensorProductOfCrystals(C,D,C.list()[0],D.list()[0])

    The representation of elements is in term of the
    Berenstein-Zelevinsky-Littelmann strings [a1, a2, ...] described
    under metapost in crystals.py. Alternative representations may be
    obtained by the options format="dual_string" or format="simple".
    In the simple format, the element is represented by and integer,
    and in the dual_string format, it is represented by the
    Berenstein-Zelevinsky-Littelmann string, but the underlying
    decomposition of the long Weyl group element into simple
    reflections is changed.

    TESTS::

        sage: C = FastCrystal(['A',2],shape=[4,1])
        sage: C.cardinality()
        24
        sage: C.cartan_type()
        ['A', 2]
        sage: TestSuite(C).run()
        sage: C = FastCrystal(['B',2],shape=[4,1])
        sage: C.cardinality()
        154
        sage: TestSuite(C).run()
        sage: C = FastCrystal(['B',2],shape=[3/2,1/2])
        sage: C.cardinality()
        16
        sage: TestSuite(C).run()
        sage: C = FastCrystal(['C',2],shape=[2,1])
        sage: C.cardinality()
        16
        sage: C = FastCrystal(['C',2],shape=[3,1])
        sage: C.cardinality()
        35
        sage: TestSuite(C).run()
    """

    @staticmethod
    def __classcall__(cls, cartan_type, shape, format = "string"):
        """
        Normalizes the input arguments to ensure unique representation

        EXAMPLES::

            sage: C1 = FastCrystal(['A',2],            shape=(4,1))
            sage: C2 = FastCrystal(CartanType(['A',2]),shape=[4,1])
            sage: C1 is C2
            True
        """
        cartan_type = CartanType(cartan_type)
        shape = tuple(shape)
        if len(shape) > 2:
            raise ValueError, "The shape must have length <=2"
        shape = shape + (0,)*(2-len(shape))
        return super(FastCrystal, cls).__classcall__(cls, cartan_type, shape, format)

    def __init__(self, ct, shape, format):
        """
        EXAMPLES::

            sage: C = FastCrystal(['A',2],shape=[4,1]); C
            The fast crystal for A2 with shape [4,1]
            sage: TestSuite(C).run()
        """
        Parent.__init__(self, category = ClassicalCrystals())
#        super(FastCrystal, self).__init__(category = FiniteEnumeratedSets())
        self._cartan_type = ct
        if ct[1] != 2:
            raise NotImplementedError

        l1 = shape[0]
        l2 = shape[1]

        # For safety, delpat and gampat should be immutable

        self.delpat = []
        self.gampat = []

        if ct[0] == 'A':
            self._type_a_init(l1, l2)
        elif ct[0] == 'B' or ct[0] == 'C':
            self._type_bc_init(l1, l2)
        else:
            raise NotImplementedError

        self.format = format
        self.size = len(self.delpat)
        self._rootoperators = []
        self.shape = shape

        for i in range(self.size):
            target = [x for x in self.delpat[i]]

            target[0] = target[0]-1
            e1 = None if target not in self.delpat else self.delpat.index(target)
            target[0] = target[0]+1+1
            f1 = None if target not in self.delpat else self.delpat.index(target)

            target = [x for x in self.gampat[i]]
            target[0] = target[0]-1
            e2 = None if target not in self.gampat else self.gampat.index(target)
            target[0] = target[0]+1+1
            f2 = None if target not in self.gampat else self.gampat.index(target)

            self._rootoperators.append([e1,f1,e2,f2])

        if int(2*l1)%2 == 0:
            l1_str = "%d"%l1
            l2_str = "%d"%l2
        else:
            assert self._cartan_type[0] == 'B' and int(2*l2)%2 == 1
            l1_str = "%d/2"%int(2*l1)
            l2_str = "%d/2"%int(2*l2)
        self.rename("The fast crystal for %s2 with shape [%s,%s]"%(ct[0],l1_str,l2_str))
        self.module_generators = [self(0)]
#        self._list = ClassicalCrystal.list(self)
        self._list = super(FastCrystal, self).list()
#        self._digraph = ClassicalCrystal.digraph(self)
        self._digraph = super(FastCrystal, self).digraph()
        self._digraph_closure = self.digraph().transitive_closure()

    def _type_a_init(self, l1, l2):
        """
        EXAMPLES::

            sage: C = FastCrystal(['A',2],shape=[1,1])
            sage: C.delpat # indirect doctest
            [[0, 0, 0], [0, 1, 0], [1, 1, 0]]
            sage: C.gampat
            [[0, 0, 0], [1, 0, 0], [0, 1, 1]]
        """
        for b in range(l2,-1,-1):
            for a in range(l1,l2-1,-1):
                for c in range(a,b-1,-1):
                    a3 = l1-a
                    a2 = l1+l2-a-b
                    a1 = a-c
                    b1 = max(a3,a2-a1)
                    b2 = a1+a3
                    b3 = min(a2-a3,a1)
                    self.delpat.append([a1,a2,a3])
                    self.gampat.append([b1,b2,b3])

    def _type_bc_init(self, l1, l2):
        """
        EXAMPLES::

            sage: C = FastCrystal(['B',2],shape=[1])
            sage: len(C.delpat) # indirect doctest
            5
            sage: len(C.gampat)
            5
            sage: C = FastCrystal(['C',2],shape=[1])
            sage: len(C.delpat)
            4
            sage: len(C.gampat)
            4
        """
        if self._cartan_type[0] == 'B':
            [m1, m2] = [l1+l2, l1-l2]
        else:
            [m1, m2] = [l1, l2]
        for b in range(m2,-1,-1):
            for a in range(m1,m2-1,-1):
                for c in range(b,a+1):
                    for d in range(c,-1,-1):
                        a1 = c-d
                        a2 = m1+m2+c-a-2*b
                        a3 = m1+m2-a-b
                        a4 = m1-a
                        b1 = max(a4,2*a3-a2,a2-2*a1)
                        b2 = max(a3, a1+a4, a1+2*a3-a2)
                        b3 = min(a2, 2*a2-2*a3+a4, 2*a1+a4)
                        b4 = min(a1, a2-a3, a3-a4)
                        if self._cartan_type[0] == 'B':
                            self.delpat.append([a1,a2,a3,a4])
                            self.gampat.append([b1,b2,b3,b4])
                        else:
                            self.gampat.append([a1,a2,a3,a4])
                            self.delpat.append([b1,b2,b3,b4])

    def __call__(self, value):
        """
        EXAMPLES::

            sage: C = FastCrystal(['A',2],shape=[2,1])
            sage: C(0)
            [0, 0, 0]
            sage: C(1)
            [1, 0, 0]
            sage: x = C(0)
            sage: C(x) is x
            True
        """
        if parent(value) is self: return value
        return self.element_class(self, value, self.format)

    def list(self):
        """
        Returns a list of the elements of self.

        EXAMPLES::

            sage: C = FastCrystal(['A',2],shape=[2,1])
            sage: C.list()
            [[0, 0, 0],
             [1, 0, 0],
             [0, 1, 1],
             [0, 2, 1],
             [1, 2, 1],
             [0, 1, 0],
             [1, 1, 0],
             [2, 1, 0]]
        """
        return self._list

    def digraph(self):
        """
        Returns the digraph associated to self.

        EXAMPLES::

            sage: C = FastCrystal(['A',2],shape=[2,1])
            sage: C.digraph()
            Digraph on 8 vertices
        """
        return self._digraph

    def cmp_elements(self, x,y):
        r"""
        Returns True if and only if there is a path from x to y in the
        crystal graph.

        Because the crystal graph is classical, it is a directed acyclic
        graph which can be interpreted as a poset. This function implements
        the comparison function of this poset.

        EXAMPLES::

            sage: C = FastCrystal(['A',2],shape=[2,1])
            sage: x = C(0)
            sage: y = C(1)
            sage: C.cmp_elements(x,y)
            -1
            sage: C.cmp_elements(y,x)
            1
            sage: C.cmp_elements(x,x)
            0
        """
        assert x.parent() == self and y.parent() == self
        if self._digraph_closure.has_edge(x,y):
            return -1
        elif self._digraph_closure.has_edge(y,x):
            return 1
        else:
            return 0

    class Element(Element):
        def __init__(self, parent, value, format):
            """
            EXAMPLES::

                sage: C = FastCrystal(['A',2],shape=[2,1])
                sage: c = C(0); c
                [0, 0, 0]
                sage: C[0].parent()
                The fast crystal for A2 with shape [2,1]
                sage: TestSuite(c).run()
            """
            Element.__init__(self, parent)
            self.value = value
            self.format = format

        def weight(self):
            """
            Returns the weight of self.

            EXAMPLES::

                sage: [v.weight() for v in FastCrystal(['A',2], shape=[2,1])]
                [(2, 1, 0), (1, 2, 0), (1, 1, 1), (1, 0, 2), (0, 1, 2), (2, 0, 1), (1, 1, 1), (0, 2, 1)]
                sage: [v.weight() for v in FastCrystal(['B',2], shape=[1,0])]
                [(1, 0), (0, 1), (0, 0), (0, -1), (-1, 0)]
                sage: [v.weight() for v in FastCrystal(['B',2], shape=[1/2,1/2])]
                [(1/2, 1/2), (1/2, -1/2), (-1/2, 1/2), (-1/2, -1/2)]
                sage: [v.weight() for v in FastCrystal(['C',2], shape=[1,0])]
                [(1, 0), (0, 1), (0, -1), (-1, 0)]
                sage: [v.weight() for v in FastCrystal(['C',2], shape=[1,1])]
                [(1, 1), (1, -1), (0, 0), (-1, 1), (-1, -1)]
            """
            delpat = self.parent().delpat[self.value]
            if self.parent()._cartan_type[0] == 'A':
                delpat = delpat + [0,]
            [alpha1, alpha2] = self.parent().weight_lattice_realization().simple_roots()
            hwv = sum(self.parent().shape[i]*self.parent().weight_lattice_realization().monomial(i) for i in range(2))
            return hwv - (delpat[0]+delpat[2])*alpha1 - (delpat[1]+delpat[3])*alpha2

        def _repr_(self):
            """
            EXAMPLES::

                sage: C = FastCrystal(['A',2],shape=[2,1])
                sage: C[0]._repr_()
                '[0, 0, 0]'
            """
            if self.format == "string":
                return repr(self.parent().delpat[self.value])
            elif self.format == "dual_string":
                return repr(self.parent().gampat[self.value])
            elif self.format == "simple":
                return repr(self.value)
            else:
                raise NotImplementedError

        def __eq__(self, other):
            """
            EXAMPLES::

                sage: C = FastCrystal(['A',2],shape=[2,1])
                sage: D = FastCrystal(['B',2],shape=[2,1])
                sage: C(0) == C(0)
                True
                sage: C(1) == C(0)
                False
                sage: C(0) == D(0)
                False
            """
            return self.__class__ is other.__class__ and \
                   self.parent() == other.parent() and \
                   self.value == other.value

        def __ne__(self, other):
            """
            EXAMPLES::

                sage: C = FastCrystal(['A',2],shape=[2,1])
                sage: D = FastCrystal(['B',2],shape=[2,1])
                sage: C(0) != C(0)
                False
                sage: C(1) != C(0)
                True
                sage: C(0) != D(0)
                True
            """
            return not self == other


        def __cmp__(self, other):
            """
            EXAMPLES::

                sage: C = FastCrystal(['A',2],shape=[2,1])
                sage: C(1) < C(2)
                True
                sage: C(2) < C(1)
                False
                sage: C(2) > C(1)
                True
                sage: C(1) <= C(1)
                True
            """
            if type(self) is not type(other):
                return cmp(type(self), type(other))
            if self.parent() != other.parent():
                return cmp(self.parent(), other.parent())
            return self.parent().cmp_elements(self, other)

        def e(self, i):
            """
            Returns the action of `e_i` on self.

            EXAMPLES::

                sage: C = FastCrystal(['A',2],shape=[2,1])
                sage: C(1).e(1)
                [0, 0, 0]
                sage: C(0).e(1) is None
                True
            """
            assert i in self.index_set()
            if i == 1:
                r = self.parent()._rootoperators[self.value][0]
            else:
                r = self.parent()._rootoperators[self.value][2]
            return self.parent()(r) if r is not None else None


        def f(self, i):
            """
            Returns the action of `f_i` on self.

            EXAMPLES::

                sage: C = FastCrystal(['A',2],shape=[2,1])
                sage: C(6).f(1)
                [1, 2, 1]
                sage: C(7).f(1) is None
                True
            """
            assert i in self.index_set()
            if i == 1:
                r = self.parent()._rootoperators[self.value][1]
            else:
                r = self.parent()._rootoperators[self.value][3]
            return self.parent()(r) if r is not None else None


#FastCrystal.Element = FastCrystalElement
