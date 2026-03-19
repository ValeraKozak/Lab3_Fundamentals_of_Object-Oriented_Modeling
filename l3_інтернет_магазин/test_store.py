import unittest

from store import (
    User,
    Product,
    Order,
    Catalog,
    Admin,
    AuthenticationError,
    ProductNotFoundError,
    OutOfStockError,
    InvalidOperationError
)


class TestOnlineStore(unittest.TestCase):
    def setUp(self):
        self.user = User(1, "Іван", "ivan@example.com", "12345")
        self.admin = Admin()
        self.catalog = Catalog()

        self.product1 = Product(101, "Ноутбук", 30000.0, 5)
        self.product2 = Product(102, "Мишка", 1000.0, 10)
        self.product3 = Product(103, "Клавіатура", 2500.0, 0)

        self.catalog.addProduct(self.product1)
        self.catalog.addProduct(self.product2)
        self.catalog.addProduct(self.product3)

    def test_user_register_returns_success_message(self):
        result = self.user.register()
        self.assertEqual(result, "Користувач Іван успішно зареєстрований.")

    def test_user_login_success(self):
        result = self.user.login("ivan@example.com", "12345")
        self.assertTrue(result)
        self.assertTrue(self.user.is_logged_in)

    def test_user_login_wrong_password_raises_error(self):
        with self.assertRaises(AuthenticationError):
            self.user.login("ivan@example.com", "wrong_password")

    def test_create_order_without_login_raises_error(self):
        with self.assertRaises(AuthenticationError):
            self.user.createOrder(1)

    def test_user_can_create_order_after_login(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(1)

        self.assertIsInstance(order, Order)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, "new")
        self.assertEqual(len(self.user.viewOrders()), 1)

    def test_add_product_to_order(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(1)

        order.addProduct(self.product1, 2)

        self.assertEqual(len(order.items), 1)
        self.assertEqual(order.items[0].product.name, "Ноутбук")
        self.assertEqual(order.items[0].quantity, 2)

    def test_add_same_product_to_order_combines_quantity(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(1)

        order.addProduct(self.product2, 2)
        order.addProduct(self.product2, 3)

        self.assertEqual(len(order.items), 1)
        self.assertEqual(order.items[0].quantity, 5)

    def test_add_product_with_insufficient_stock_raises_error(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(1)

        with self.assertRaises(OutOfStockError):
            order.addProduct(self.product1, 100)

    def test_remove_product_from_order(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(1)

        order.addProduct(self.product1, 1)
        order.addProduct(self.product2, 2)
        order.removeProduct(self.product1.id)

        self.assertEqual(len(order.items), 1)
        self.assertEqual(order.items[0].product.id, self.product2.id)

    def test_calculate_total(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(1)

        order.addProduct(self.product1, 1)  # 30000
        order.addProduct(self.product2, 2)  # 2000

        self.assertEqual(order.calculateTotal(), 32000.0)

    def test_checkout_changes_status_and_reduces_stock(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(1)

        order.addProduct(self.product1, 2)
        order.addProduct(self.product2, 3)
        order.checkout()

        self.assertEqual(order.status, "placed")
        self.assertEqual(self.product1.stock, 3)
        self.assertEqual(self.product2.stock, 7)

    def test_checkout_empty_order_raises_error(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(1)

        with self.assertRaises(InvalidOperationError):
            order.checkout()

    def test_catalog_search_products(self):
        results = self.catalog.searchProducts("миш")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Мишка")

    def test_admin_can_update_product_stock(self):
        self.admin.updateProductStock(self.catalog, 101, 20)
        product = self.catalog.findProductById(101)

        self.assertEqual(product.stock, 20)

    def test_admin_can_remove_product_from_catalog(self):
        self.admin.removeProduct(self.catalog, 102)

        with self.assertRaises(ProductNotFoundError):
            self.catalog.findProductById(102)

    def test_full_user_order_interaction(self):
        self.user.login("ivan@example.com", "12345")
        order = self.user.createOrder(555)

        order.addProduct(self.product1, 1)
        order.addProduct(self.product2, 2)

        self.assertEqual(order.user, self.user)
        self.assertEqual(len(order.items), 2)
        self.assertEqual(order.getItemsCount(), 3)
        self.assertEqual(order.calculateTotal(), 32000.0)

        order.checkout()

        self.assertIn(order, self.user.viewOrders())
        self.assertEqual(order.status, "placed")


if __name__ == "__main__":
    unittest.main()