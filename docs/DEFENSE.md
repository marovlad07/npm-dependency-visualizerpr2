# Порядок демонстрации на защите

Все команды запускаются в PowerShell из корневой папки проекта.
Первые четыре этапа можно показать без Интернета через тестовый репозиторий.

## 1. Конфигурация и ошибки

```powershell
.\run.bat --package is-odd --version 3.0.1 --mode config
.\run.bat --package "BAD!" --version 3.0.1 --mode config
.\run.bat --package is-odd --version wrong --mode config
.\run.bat --package is-odd --version 3.0.1 --repository wrong --mode config
.\run.bat --test maybe --package A --version 1.0.0 --mode config
.\run.bat --test --package A --version 1.0.0 --repository absent.json
```

Первая команда показывает параметры. Остальные намеренно завершаются
ошибкой и кодом 2. Отсутствующие обязательные параметры и неизвестные
режимы также обрабатывает `argparse`.

## 2. Прямые зависимости

```powershell
.\run.bat --package is-odd --version 3.0.1 --mode direct
```

Ожидается `is-number: ^6.0.0`. Источник данных — объект
`versions["3.0.1"].dependencies`, а не последняя версия пакета.

Офлайн-аналог:

```powershell
.\run.bat --test --repository examples/chain.json --package A --version 1.0.0 --mode direct
```

## 3. BFS и циклы

```powershell
.\run.bat --test --repository examples/diamond.json --package A --version 1.0.0
.\run.bat --test --repository examples/cycle.json --package A --version 1.0.0
.\run.bat --test --repository examples/self.json --package A --version 1.0.0
.\run.bat --test --repository examples/versions.json --package A --version 1.0.0
```

Ромб дает 4 узла и 4 ребра; цикл — 3 узла и 3 ребра; петля — один узел
и одно ребро. В `versions` B@1.2.0 и B@2.0.0 остаются разными узлами.

Объяснение алгоритма: в очереди сначала корень. Извлекаем первый пакет,
получаем его прямые зависимости и добавляем новые узлы в конец очереди.
Пакет помечается обнаруженным сразу при добавлении. Если узел уже
обнаружен, повторно в очередь он не попадает, но ребро сохраняется.

## 4. Обратные зависимости

```powershell
.\run.bat --test --repository examples/diamond.json --package D --version 1.0.0 --mode reverse
.\run.bat --test --repository examples/cycle.json --package A --version 1.0.0 --mode reverse
.\run.bat --test --repository examples/empty.json --package A --version 1.0.0 --mode reverse
```

Для D в ромбе прямые родители — B и C, все родители — B, C, A.
Используется тот же BFS, но направления ребер предварительно меняются.
Тестовый файл анализируется целиком. В реальном npm поиск ограничен
графом, достижимым из выбранного корневого пакета.

## 5. Изображения и сравнение

```powershell
.\demo_all.bat
```

Откроется галерея трех пакетов. Штатный вывод npm и объяснение сравнения
находятся в [COMPARISON.md](COMPARISON.md) и `results/*-npm-tree.txt`.

Офлайн-визуализация:

```powershell
.\demo.bat
```

## Тесты и история

```powershell
.\test.bat
git log --oneline --reverse
```

Отдельные коммиты соответствуют этапам. Исходники не вызывают npm:
поиск зависимостей реализован на Python через `urllib` и `json`.
Graphviz вызывается только после построения графа, для рисования.
