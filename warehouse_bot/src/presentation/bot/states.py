from aiogram.fsm.state import StatesGroup, State


class WarehouseActivation(StatesGroup):
    """Состояния для активации склада."""
    waiting_for_activation_code = State()  # Ожидание ввода кода активации


class OrderProcessing(StatesGroup):
    """Состояния для обработки заказа."""
    waiting_for_cooking_time = State()    # После принятия заказа — ожидание времени готовки
    waiting_for_photos = State()          # После нажатия "Заказ готов" — ожидание фото