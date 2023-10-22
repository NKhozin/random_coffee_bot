## MeetCafeBot
#### MeetCafeBot - это ваш незаменимый помощник для создания новых знакомств в группе Telegram. Созданный для организации случайных встреч за чашкой кофе, этот бот объединяет участников группы в пары для непринужденных бесед один на один.
### Описание файлов:
- bot	- основной файл с логикой формирования пар и обработкой сообщений от пользователей.
- db_commands - файл с функциями для взаимодействия с базой данных.
  
### В текущей версии бота реализовано:
1. Логирование пользователей при событии присоединения к чату, а также при событии выхода из него. В библиотеке python-telegram-bot отсутствует возможность получения полного списка участников чата.
2. Обработка сообщений пользователей с информацией об удобном времени для встречи. Преобразование входных данных в виде временных интервалов в список всех возможных вариантов  для начала встречи кратных 30 минутам из этого интервала. Логирование этой информации в базу данных.
3. Рекурсивный алгоритм формирования пар пользователей:
-  учитывается пересечение свободных временных интервалов между пользователям
- проверяется наличие свободных комнат. Учет свободных комнат и логирование их занятости происходит в базе данных.
- проверяется факт пересечение планируемой встречи с тем, что у пользователя уже запланирована встреча с другим пользователем на это время
- проверяется факт того, что у пользователей уже была встреча
- проверяется условие на то, что все возможные встречи уже запланированы или прошли. Проверка происходит по сравнению количества всех возможных пар для встреч и количества встреч, которые запланированы или прошли. В случае не совпадения этого количества происходит поиск пользователей, которые не поучаствовали в встречах. Им направляется сообщение о том, что необходимо выбрать дополнительные временные интервалы, так как сейчас: 1) нет подходящей пары по времени; 2) все комнаты заняты.
4. Обращение к пользователем по гиперссылке. Таким образом, данное уведомление будет выделяться на фоне остальных сообщений в мессенджере.
5. Отправка уведомлений пользователям в личные сообщения о предстоящих встречах.
6. Удобное визуальное представление предстоящей встречи в табличном формате с указанием о том, где, когда, во сколько будет встреча, а также кто ее участники.
7. Изменение статусов встреч по команде бота, если текущее время больше, чем время окончания встречи. 
8. Удаление истории встреч в базе данных по команде бота. Например, для возможности создать новый круг встреч.
9. Логирование всех ключевых этапов работы бота. Благодаря этому в будущем возможно реализовать аналитику по встречам.

### Возможные дальнейшие шаги по развитию бота:
1. Автоматическое добавление встречи в календарь.
2. Оповещение участников о предстоящей встрече за некоторые время. Например, за 5 минут.
3. Получение от пользователей обратной связи по прошедшим встречам. На основе этой информации исключение некоторых участников из подбора.
4. Поддержка тематических встреч: дать возможность пользователям указывать интересы или темы, которые их интересуют, и затем подбирать партнеров по интересам.
5. Групповые встречи для пользователей, которые дали на это согласие.
6. Предоставление аналитики и статистики. Например, среднее и максимальное время одного разговора, общее время общения в месяц, максимальное количество встреч в сутки и так далее. Также можно формировать топы пользователей по различным критериям и поощрять самых лучших. Например, самый активный пользователь за месяц. 

### Варианты монетизации:
1. Премиум подписка, в которой будет:
- доступно большее количество встреч в месяц
- доступна функция групповой встречи
- возможность блокировать некоторых пользователей
- фильтрация пользователей по их рейтингу
- отсутствие рекламы
- более продвинутый алгоритм подбора с использованием искусственного интеллекта
2. Реклама внутри бота.
3. Организация различных платных событий среди участников чата. Например, проведение коллективной игры в мафию с привлечением профессионального ведущего.
4. Донаты в знак благодарности.
