-- Очистка старых категорий (опционально, закомментируйте если не нужно)
-- DELETE FROM categories;

-- Arduino
INSERT INTO categories (name, parent_id) VALUES ('Arduino', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Модуль', (SELECT id FROM categories WHERE name = 'Arduino' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Плата', (SELECT id FROM categories WHERE name = 'Arduino' AND parent_id IS NULL));

-- СИС
INSERT INTO categories (name, parent_id) VALUES ('СИС', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Направляющая', (SELECT id FROM categories WHERE name = 'СИС' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Вал 10 мм', (SELECT id FROM categories WHERE name = 'Направляющая' AND parent_id = (SELECT id FROM categories WHERE name = 'СИС' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Вал 16 мм', (SELECT id FROM categories WHERE name = 'Направляющая' AND parent_id = (SELECT id FROM categories WHERE name = 'СИС' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Подшипник', (SELECT id FROM categories WHERE name = 'СИС' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Линейный', (SELECT id FROM categories WHERE name = 'Подшипник' AND parent_id = (SELECT id FROM categories WHERE name = 'СИС' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Обычный', (SELECT id FROM categories WHERE name = 'Подшипник' AND parent_id = (SELECT id FROM categories WHERE name = 'СИС' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Опорный', (SELECT id FROM categories WHERE name = 'Подшипник' AND parent_id = (SELECT id FROM categories WHERE name = 'СИС' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Ремень', (SELECT id FROM categories WHERE name = 'СИС' AND parent_id IS NULL));

-- DC - DC
INSERT INTO categories (name, parent_id) VALUES ('DC - DC', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Повышающий', (SELECT id FROM categories WHERE name = 'DC - DC' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Понижающий', (SELECT id FROM categories WHERE name = 'DC - DC' AND parent_id IS NULL));

-- Акустика
INSERT INTO categories (name, parent_id) VALUES ('Акустика', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Микрофон', (SELECT id FROM categories WHERE name = 'Акустика' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Электретный', (SELECT id FROM categories WHERE name = 'Микрофон' AND parent_id = (SELECT id FROM categories WHERE name = 'Акустика' AND parent_id IS NULL)));

-- Датчик
INSERT INTO categories (name, parent_id) VALUES ('Датчик', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Температуры', (SELECT id FROM categories WHERE name = 'Датчик' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Термистор', (SELECT id FROM categories WHERE name = 'Температуры' AND parent_id = (SELECT id FROM categories WHERE name = 'Датчик' AND parent_id IS NULL)));

-- Диод
INSERT INTO categories (name, parent_id) VALUES ('Диод', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Быстродействующий', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Варикап', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Выпрямительный', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Высоковольтный', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Диодная сборка', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Мост', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Силовой', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Стабилитрон', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Шоттки', (SELECT id FROM categories WHERE name = 'Диод' AND parent_id IS NULL));

-- Индуктивность
INSERT INTO categories (name, parent_id) VALUES ('Индуктивность', NULL);
INSERT INTO categories (name, parent_id) VALUES ('0307 0.25W', (SELECT id FROM categories WHERE name = 'Индуктивность' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('0510 1W', (SELECT id FROM categories WHERE name = 'Индуктивность' AND parent_id IS NULL));

-- Кнопки, переключатели
INSERT INTO categories (name, parent_id) VALUES ('Кнопки, переключатели', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Внешний', (SELECT id FROM categories WHERE name = 'Кнопки, переключатели' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Для корпуса', (SELECT id FROM categories WHERE name = 'Кнопки, переключатели' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Для плат', (SELECT id FROM categories WHERE name = 'Кнопки, переключатели' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Тактовая кнопка', (SELECT id FROM categories WHERE name = 'Кнопки, переключатели' AND parent_id IS NULL));

-- Компьютер
INSERT INTO categories (name, parent_id) VALUES ('Компьютер', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Оперативная память', (SELECT id FROM categories WHERE name = 'Компьютер' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('DDR1', (SELECT id FROM categories WHERE name = 'Оперативная память' AND parent_id = (SELECT id FROM categories WHERE name = 'Компьютер' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('DDR2', (SELECT id FROM categories WHERE name = 'Оперативная память' AND parent_id = (SELECT id FROM categories WHERE name = 'Компьютер' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('DDR3', (SELECT id FROM categories WHERE name = 'Оперативная память' AND parent_id = (SELECT id FROM categories WHERE name = 'Компьютер' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('DDR4', (SELECT id FROM categories WHERE name = 'Оперативная память' AND parent_id = (SELECT id FROM categories WHERE name = 'Компьютер' AND parent_id IS NULL)));

-- Конденсатор
INSERT INTO categories (name, parent_id) VALUES ('Конденсатор', NULL);
INSERT INTO categories (name, parent_id) VALUES ('SMD', (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('0805', (SELECT id FROM categories WHERE name = 'SMD' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('1206', (SELECT id FROM categories WHERE name = 'SMD' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Керамический', (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('NPO', (SELECT id FROM categories WHERE name = 'Керамический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Высоковольтный', (SELECT id FROM categories WHERE name = 'Керамический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Дисковый', (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('3мм', (SELECT id FROM categories WHERE name = 'Дисковый' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('5мм', (SELECT id FROM categories WHERE name = 'Дисковый' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Квадратный', (SELECT id FROM categories WHERE name = 'Дисковый' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Пленочный', (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('200V', (SELECT id FROM categories WHERE name = 'Пленочный' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('250V', (SELECT id FROM categories WHERE name = 'Пленочный' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('400V', (SELECT id FROM categories WHERE name = 'Пленочный' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('630V', (SELECT id FROM categories WHERE name = 'Пленочный' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Высоковольтный', (SELECT id FROM categories WHERE name = 'Пленочный' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('1.6kV', (SELECT id FROM categories WHERE name = 'Высоковольтный' AND parent_id IN (SELECT id FROM categories WHERE name = 'Пленочный')));
INSERT INTO categories (name, parent_id) VALUES ('3kV', (SELECT id FROM categories WHERE name = 'Высоковольтный' AND parent_id IN (SELECT id FROM categories WHERE name = 'Пленочный')));
INSERT INTO categories (name, parent_id) VALUES ('5kV', (SELECT id FROM categories WHERE name = 'Высоковольтный' AND parent_id IN (SELECT id FROM categories WHERE name = 'Пленочный')));
INSERT INTO categories (name, parent_id) VALUES ('6.3kV', (SELECT id FROM categories WHERE name = 'Высоковольтный' AND parent_id IN (SELECT id FROM categories WHERE name = 'Пленочный')));
INSERT INTO categories (name, parent_id) VALUES ('Полипропиленовый', (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('250V', (SELECT id FROM categories WHERE name = 'Полипропиленовый' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('275V', (SELECT id FROM categories WHERE name = 'Полипропиленовый' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('310V', (SELECT id FROM categories WHERE name = 'Полипропиленовый' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Электролитический', (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('100V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('10V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('160V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('16V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('200V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('250V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('25V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('280V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('350V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('35V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('400V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('450V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('50V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('5kV', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('6.3V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('63V', (SELECT id FROM categories WHERE name = 'Электролитический' AND parent_id = (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Суперконденсатор', (SELECT id FROM categories WHERE name = 'Конденсатор' AND parent_id IS NULL));

-- Микросхемы
INSERT INTO categories (name, parent_id) VALUES ('Микросхемы', NULL);
INSERT INTO categories (name, parent_id) VALUES ('AVR', (SELECT id FROM categories WHERE name = 'Микросхемы' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('EEPROM', (SELECT id FROM categories WHERE name = 'AVR' AND parent_id = (SELECT id FROM categories WHERE name = 'Микросхемы' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Микроконтроллер', (SELECT id FROM categories WHERE name = 'AVR' AND parent_id = (SELECT id FROM categories WHERE name = 'Микросхемы' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Отечественные', (SELECT id FROM categories WHERE name = 'Микросхемы' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Панелька', (SELECT id FROM categories WHERE name = 'Микросхемы' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Сборка Дарлингтона', (SELECT id FROM categories WHERE name = 'Микросхемы' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('УНЧ', (SELECT id FROM categories WHERE name = 'Микросхемы' AND parent_id IS NULL));

-- Оптоэлектроника
INSERT INTO categories (name, parent_id) VALUES ('Оптоэлектроника', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Индикаторы и дисплеи', (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('LCD', (SELECT id FROM categories WHERE name = 'Индикаторы и дисплеи' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('LED', (SELECT id FROM categories WHERE name = 'Индикаторы и дисплеи' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('7 сегментный 1 разряд', (SELECT id FROM categories WHERE name = 'LED' AND parent_id IN (SELECT id FROM categories WHERE name = 'Индикаторы и дисплеи')));
INSERT INTO categories (name, parent_id) VALUES ('7 сегментный 2 разряда', (SELECT id FROM categories WHERE name = 'LED' AND parent_id IN (SELECT id FROM categories WHERE name = 'Индикаторы и дисплеи')));
INSERT INTO categories (name, parent_id) VALUES ('7 сегментный 4 разряда', (SELECT id FROM categories WHERE name = 'LED' AND parent_id IN (SELECT id FROM categories WHERE name = 'Индикаторы и дисплеи')));
INSERT INTO categories (name, parent_id) VALUES ('Лампа', (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Оптопара', (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Светодиод', (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('10 мм', (SELECT id FROM categories WHERE name = 'Светодиод' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('3 мм', (SELECT id FROM categories WHERE name = 'Светодиод' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('5 мм', (SELECT id FROM categories WHERE name = 'Светодиод' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('RGB', (SELECT id FROM categories WHERE name = 'Светодиод' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('SMD', (SELECT id FROM categories WHERE name = 'Светодиод' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('0805', (SELECT id FROM categories WHERE name = 'SMD' AND parent_id IN (SELECT id FROM categories WHERE name = 'Светодиод')));
INSERT INTO categories (name, parent_id) VALUES ('1206', (SELECT id FROM categories WHERE name = 'SMD' AND parent_id IN (SELECT id FROM categories WHERE name = 'Светодиод')));
INSERT INTO categories (name, parent_id) VALUES ('ИК', (SELECT id FROM categories WHERE name = 'Светодиод' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Мощный', (SELECT id FROM categories WHERE name = 'Светодиод' AND parent_id = (SELECT id FROM categories WHERE name = 'Оптоэлектроника' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('1W', (SELECT id FROM categories WHERE name = 'Мощный' AND parent_id IN (SELECT id FROM categories WHERE name = 'Светодиод')));
INSERT INTO categories (name, parent_id) VALUES ('3W', (SELECT id FROM categories WHERE name = 'Мощный' AND parent_id IN (SELECT id FROM categories WHERE name = 'Светодиод')));

-- Предохранитель
INSERT INTO categories (name, parent_id) VALUES ('Предохранитель', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Держатель для корпуса', (SELECT id FROM categories WHERE name = 'Предохранитель' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Держатель для платы', (SELECT id FROM categories WHERE name = 'Предохранитель' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Стекло 5x20', (SELECT id FROM categories WHERE name = 'Предохранитель' AND parent_id IS NULL));

-- Радиолампы
INSERT INTO categories (name, parent_id) VALUES ('Радиолампы', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Газоразрядный индикатор', (SELECT id FROM categories WHERE name = 'Радиолампы' AND parent_id IS NULL));

-- Разъем
INSERT INTO categories (name, parent_id) VALUES ('Разъем', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Внешний', (SELECT id FROM categories WHERE name = 'Разъем' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Для корпуса', (SELECT id FROM categories WHERE name = 'Разъем' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Для плат', (SELECT id FROM categories WHERE name = 'Разъем' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Клеммник', (SELECT id FROM categories WHERE name = 'Разъем' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Для плат', (SELECT id FROM categories WHERE name = 'Клеммник' AND parent_id = (SELECT id FROM categories WHERE name = 'Разъем' AND parent_id IS NULL)));

-- Резистор
INSERT INTO categories (name, parent_id) VALUES ('Резистор', NULL);
INSERT INTO categories (name, parent_id) VALUES ('SMD', (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('0805', (SELECT id FROM categories WHERE name = 'SMD' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('1206', (SELECT id FROM categories WHERE name = 'SMD' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Выводной', (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('0.125 W', (SELECT id FROM categories WHERE name = 'Выводной' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('0.25 W', (SELECT id FROM categories WHERE name = 'Выводной' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('0.5 W', (SELECT id FROM categories WHERE name = 'Выводной' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('1 W', (SELECT id FROM categories WHERE name = 'Выводной' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('2 W', (SELECT id FROM categories WHERE name = 'Выводной' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('5 W', (SELECT id FROM categories WHERE name = 'Выводной' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('7 W', (SELECT id FROM categories WHERE name = 'Выводной' AND parent_id = (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Переменный', (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Подстроечный', (SELECT id FROM categories WHERE name = 'Резистор' AND parent_id IS NULL));

-- Резонаторы и фильтры
INSERT INTO categories (name, parent_id) VALUES ('Резонаторы и фильтры', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Кварцевый резонатор', (SELECT id FROM categories WHERE name = 'Резонаторы и фильтры' AND parent_id IS NULL));

-- Реле
INSERT INTO categories (name, parent_id) VALUES ('Реле', NULL);

-- Симистор
INSERT INTO categories (name, parent_id) VALUES ('Симистор', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Импортный', (SELECT id FROM categories WHERE name = 'Симистор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Отечественный', (SELECT id FROM categories WHERE name = 'Симистор' AND parent_id IS NULL));

-- Тиристор
INSERT INTO categories (name, parent_id) VALUES ('Тиристор', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Импортный', (SELECT id FROM categories WHERE name = 'Тиристор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('Отечественный', (SELECT id FROM categories WHERE name = 'Тиристор' AND parent_id IS NULL));

-- Транзистор
INSERT INTO categories (name, parent_id) VALUES ('Транзистор', NULL);
INSERT INTO categories (name, parent_id) VALUES ('Зарубежный', (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('MOSFET N - канал', (SELECT id FROM categories WHERE name = 'Зарубежный' AND parent_id = (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('MOSFET P - канал', (SELECT id FROM categories WHERE name = 'Зарубежный' AND parent_id = (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('NPN', (SELECT id FROM categories WHERE name = 'Зарубежный' AND parent_id = (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Высокочастотный', (SELECT id FROM categories WHERE name = 'NPN' AND parent_id IN (SELECT id FROM categories WHERE name = 'Зарубежный')));
INSERT INTO categories (name, parent_id) VALUES ('Мощный', (SELECT id FROM categories WHERE name = 'NPN' AND parent_id IN (SELECT id FROM categories WHERE name = 'Зарубежный')));
INSERT INTO categories (name, parent_id) VALUES ('Обычный', (SELECT id FROM categories WHERE name = 'NPN' AND parent_id IN (SELECT id FROM categories WHERE name = 'Зарубежный')));
INSERT INTO categories (name, parent_id) VALUES ('Отечественный', (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL));
INSERT INTO categories (name, parent_id) VALUES ('MOSFET N - канал', (SELECT id FROM categories WHERE name = 'Отечественный' AND parent_id = (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('MOSFET P - канал', (SELECT id FROM categories WHERE name = 'Отечественный' AND parent_id = (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('NPN', (SELECT id FROM categories WHERE name = 'Отечественный' AND parent_id = (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Высокочастотный', (SELECT id FROM categories WHERE name = 'NPN' AND parent_id IN (SELECT id FROM categories WHERE name = 'Отечественный')));
INSERT INTO categories (name, parent_id) VALUES ('PNP', (SELECT id FROM categories WHERE name = 'Отечественный' AND parent_id = (SELECT id FROM categories WHERE name = 'Транзистор' AND parent_id IS NULL)));
INSERT INTO categories (name, parent_id) VALUES ('Высокочастотный', (SELECT id FROM categories WHERE name = 'PNP' AND parent_id IN (SELECT id FROM categories WHERE name = 'Отечественный')));
INSERT INTO categories (name, parent_id) VALUES ('Обычный', (SELECT id FROM categories WHERE name = 'PNP' AND parent_id IN (SELECT id FROM categories WHERE name = 'Отечественный')));