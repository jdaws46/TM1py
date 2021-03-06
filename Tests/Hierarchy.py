import configparser
import os
import unittest

from TM1py.Objects import Dimension, Hierarchy, Subset
from TM1py.Services import TM1Service

config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'))

DIMENSION_PREFIX = 'TM1py_Tests_Hierarchy_'
DIMENSION_NAME = DIMENSION_PREFIX + "Some_Name"
SUBSET_NAME = DIMENSION_PREFIX + "Some_Subset"


class TestHierarchyMethods(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.tm1 = TM1Service(**config['tm1srv01'])

    @classmethod
    def teardown_class(cls):
        cls.tm1.logout()

    @classmethod
    def setUp(cls):
        cls.create_dimension()
        cls.create_subset()

    @classmethod
    def tearDown(cls):
        cls.delete_dimension()

    @classmethod
    def create_dimension(cls):
        d = Dimension(DIMENSION_NAME)
        h = Hierarchy(DIMENSION_NAME, DIMENSION_NAME)
        h.add_element('Total Years', 'Consolidated')
        h.add_element('No Year', 'Numeric')
        h.add_element('1989', 'Numeric')
        h.add_element("Marius's Element", "Numeric")
        h.add_element_attribute('Previous Year', 'String')
        h.add_element_attribute('Next Year', 'String')
        h.add_edge('Total Years', '1989', 2)
        d.add_hierarchy(h)
        cls.tm1.dimensions.create(d)

    @classmethod
    def delete_dimension(cls):
        cls.tm1.dimensions.delete(DIMENSION_NAME)

    @classmethod
    def create_subset(cls):
        s = Subset(SUBSET_NAME, DIMENSION_NAME, DIMENSION_NAME,
                   expression="{{[{}].Members}}".format(DIMENSION_NAME))
        cls.tm1.dimensions.subsets.create(s, False)

    def test_get_hierarchy(self):
        h = self.tm1.dimensions.hierarchies.get(DIMENSION_NAME, DIMENSION_NAME)
        self.assertIn('Total Years', h.elements.keys())
        self.assertIn('No Year', h.elements.keys())
        self.assertIn('1989', h.elements.keys())
        self.assertIn('Next Year', [ea.name for ea in h.element_attributes])
        self.assertIn('Previous Year', [ea.name for ea in h.element_attributes])
        self.assertIn(SUBSET_NAME, h.subsets)

    def test_update_hierarchy(self):
        # Get dimension and hierarchy
        d = self.tm1.dimensions.get(dimension_name=DIMENSION_NAME)
        h = d.default_hierarchy
        # Edit Elements and Edges
        for year in range(2010, 2021, 1):
            parent = str(year)
            h.add_element(parent, 'Consolidated')
            h.add_edge('Total Years', parent, 1)
            for month in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'):
                component = '{}-{}'.format(year, month)
                h.add_element(component, 'Numeric')
                h.add_edge(parent, component, 1)
        # Edit Element Attributes
        h.add_element_attribute('Name Long', 'Alias')
        h.add_element_attribute('Name Short', 'Alias')
        h.add_element_attribute('Days', 'Numeric')
        # Remove attribute
        h.remove_element_attribute('Next Year')
        # Remove Edge
        h.remove_edge('Total Years', '1989')
        # Update Edge
        h.update_edge('Total Years', '2011', 2)
        # Update_element
        h.update_element('No Year', 'String')
        self.tm1.dimensions.update(d)

        # Check if update works
        d = self.tm1.dimensions.get(DIMENSION_NAME)
        h = d.default_hierarchy
        self.assertIn('2010-Jan', h.elements.keys())
        self.assertIn('2020-Dec', h.elements.keys())

        self.assertNotIn('Next Year', [ea.name for ea in h.element_attributes])
        self.assertIn('Previous Year', [ea.name for ea in h.element_attributes])
        self.assertIn('Days', [ea.name for ea in h.element_attributes])
        self.assertIn('Name Long', [ea.name for ea in h.element_attributes])

        self.assertEqual(h.edges[('Total Years', '2011')], 2)
        self.assertEqual(h.elements['No Year'].element_type, 'String')

        summary = self.tm1.dimensions.hierarchies.get_hierarchy_summary(DIMENSION_NAME, DIMENSION_NAME)
        self.assertEqual(summary["Elements"], 147)
        self.assertEqual(summary["Edges"], 143)
        self.assertEqual(summary["Members"], 147)
        self.assertEqual(summary["ElementAttributes"], 4)
        self.assertEqual(summary["Levels"], 3)

    def test_hierarchy_summary(self):
        summary = self.tm1.dimensions.hierarchies.get_hierarchy_summary(DIMENSION_NAME, DIMENSION_NAME)
        self.assertEqual(summary["Elements"], 4)
        self.assertEqual(summary["Edges"], 1)
        self.assertEqual(summary["Members"], 4)
        self.assertEqual(summary["ElementAttributes"], 2)
        self.assertEqual(summary["Levels"], 2)


if __name__ == '__main__':
    unittest.main()
