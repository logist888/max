// Единая точка для внешней ссылки на скрининг/диагностику. Все инлайновые
// «тест»-ссылки и редирект /test/ берут URL отсюда — менять/откатывать в одном
// месте. Открываются в новом окне (target="_blank"). Конверсионные блоки <Cta>
// берут URL из config/goals.json (цель diagnostic) с UTM-метками по типу страницы.
export const SCREENING_URL = 'https://mainexperts.online/screening';
