// Единая точка для внешней ссылки на скрининг/диагностику (временная страница
// dev.mainexperts.online). Все инлайновые «тест»-ссылки и редирект /test/ берут
// URL отсюда — менять/откатывать в одном месте. Конверсионные блоки <Cta> берут
// URL из config/goals.json (цель diagnostic) с UTM-метками по типу страницы.
export const SCREENING_URL = 'https://dev.mainexperts.online/screening';
