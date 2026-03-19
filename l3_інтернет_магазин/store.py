from dataclasses import dataclass, field
from typing import List


class StoreError(Exception):
    pass


class AuthenticationError(StoreError):
    pass


class ProductNotFoundError(StoreError):
    pass


class OutOfStockError(StoreError):
    pass


class InvalidOperationError(StoreError):
    pass


@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Ціна не може бути від'ємною.")
        if self.stock < 0:
            raise ValueError("Кількість на складі не може бути від'ємною.")

    def updateStock(self, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Кількість на складі не може бути від'ємною.")
        self.stock = quantity

    def isAvailable(self, quantity: int) -> bool:
        if quantity <= 0:
            return False
        return self.stock >= quantity


@dataclass
class OrderItem:
    product: Product
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Кількість товару повинна бути більшою за 0.")

    def getSubtotal(self) -> float:
        return self.product.price * self.quantity


@dataclass
class Catalog:
    products: List[Product] = field(default_factory=list)

    def addProduct(self, product: Product) -> None:
        if self.findProductById(product.id, raise_error=False) is not None:
            raise InvalidOperationError(f"Товар з id={product.id} вже існує.")
        self.products.append(product)

    def removeProduct(self, product_id: int) -> None:
        product = self.findProductById(product_id)
        self.products.remove(product)

    def findProductById(self, product_id: int, raise_error: bool = True):
        for product in self.products:
            if product.id == product_id:
                return product

        if raise_error:
            raise ProductNotFoundError(f"Товар з id={product_id} не знайдено.")
        return None

    def searchProducts(self, keyword: str) -> List[Product]:
        keyword = keyword.strip().lower()
        if not keyword:
            return self.products.copy()

        return [p for p in self.products if keyword in p.name.lower()]

    def listProducts(self) -> List[Product]:
        return self.products.copy()


@dataclass
class User:
    id: int
    name: str
    email: str
    password: str
    is_logged_in: bool = False
    _orders: List["Order"] = field(default_factory=list, init=False, repr=False)

    def register(self) -> str:
        return f"Користувач {self.name} успішно зареєстрований."

    def login(self, email: str, password: str) -> bool:
        if self.email == email and self.password == password:
            self.is_logged_in = True
            return True
        raise AuthenticationError("Невірний email або пароль.")

    def logout(self) -> None:
        self.is_logged_in = False

    def createOrder(self, order_id: int) -> "Order":
        if not self.is_logged_in:
            raise AuthenticationError("Користувач повинен увійти в систему.")
        order = Order(id=order_id, user=self)
        self._orders.append(order)
        return order

    def viewOrders(self) -> List["Order"]:
        return self._orders.copy()


@dataclass
class Order:
    id: int
    user: User
    items: List[OrderItem] = field(default_factory=list)
    status: str = "new"

    def addProduct(self, product: Product, quantity: int) -> None:
        if self.status != "new":
            raise InvalidOperationError("Не можна змінювати вже оформлене замовлення.")

        if quantity <= 0:
            raise ValueError("Кількість повинна бути більшою за 0.")

        if not product.isAvailable(quantity):
            raise OutOfStockError("Недостатньо товару на складі.")

        for item in self.items:
            if item.product.id == product.id:
                new_quantity = item.quantity + quantity
                if not product.isAvailable(new_quantity):
                    raise OutOfStockError("Недостатньо товару на складі для збільшення кількості.")
                item.quantity = new_quantity
                return

        self.items.append(OrderItem(product=product, quantity=quantity))

    def removeProduct(self, product_id: int) -> None:
        if self.status != "new":
            raise InvalidOperationError("Не можна змінювати вже оформлене замовлення.")

        for item in self.items:
            if item.product.id == product_id:
                self.items.remove(item)
                return

        raise ProductNotFoundError(f"Товар з id={product_id} відсутній у замовленні.")

    def calculateTotal(self) -> float:
        return sum(item.getSubtotal() for item in self.items)

    def getItemsCount(self) -> int:
        return sum(item.quantity for item in self.items)

    def checkout(self) -> None:
        if self.status != "new":
            raise InvalidOperationError("Замовлення вже оформлене.")

        if not self.items:
            raise InvalidOperationError("Неможливо оформити порожнє замовлення.")

        for item in self.items:
            if not item.product.isAvailable(item.quantity):
                raise OutOfStockError(
                    f"Недостатньо товару '{item.product.name}' на складі."
                )

        for item in self.items:
            item.product.stock -= item.quantity

        self.status = "placed"


@dataclass
class Admin:
    def addProduct(self, catalog: Catalog, product: Product) -> None:
        catalog.addProduct(product)

    def removeProduct(self, catalog: Catalog, product_id: int) -> None:
        catalog.removeProduct(product_id)

    def updateProductStock(self, catalog: Catalog, product_id: int, stock: int) -> None:
        product = catalog.findProductById(product_id)
        product.updateStock(stock)
