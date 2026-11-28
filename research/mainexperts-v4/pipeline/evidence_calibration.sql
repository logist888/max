-- Independent commercial review. Keep every machine candidate and the reason for any change.
CREATE OR REPLACE TABLE commercial_review AS
WITH candidates AS (
 SELECT q.query_id, l.service_id AS machine_service_id, l.intent_id AS machine_intent_id,
        l.cluster_base_id AS machine_cluster_base_id, l.evidence_level AS machine_evidence_level,
 CASE
  WHEN l.service_id='P04' AND l.cluster_base_id='K113' THEN 'program_title_not_provider'
  WHEN l.service_id='P21' AND regexp_matches(q.query_normalized, '^(master|msc|mba|bachelor|licen[cs]e|degree) (of |in |de |en )?(consulting|education consult)') THEN 'program_title_not_provider'
  WHEN l.service_id='P11' AND q.query_normalized='university application consultant' THEN 'reroute_adviser'
  WHEN l.service_id='P23' AND regexp_matches(q.query_normalized, '(\btutor(s|ing)?\b|репетитор)') THEN 'reroute_tutoring'
  WHEN l.service_id='P23' AND regexp_matches(q.query_normalized, '(tips from|personal statement reviewer$)') THEN 'information_or_free_tool'
  WHEN l.service_id='P23' AND q.query_normalized='personal statement service' AND contains(coalesce(q.target_url,''),'ucas.com/') THEN 'information_or_free_tool'
  WHEN l.service_id='P20' AND regexp_matches(q.query_normalized, '^(border patrol agent |как стать|как начать работать|как работать репетитором|как устроиться репетитором)|обязанности репетитора|обязанности.{0,25}репетитор|сколько зарабатыва|сколько получает репетитор|сколько платят репетиторам|зарплата репетитор|курс для репетитор|учеников (для |)репетитор|резюме репетитор|сайты для репетиторов|обучение (на репетитора|репетиторству)|платформы для репетитор|форум репетиторов|ресурсы для репетитора|как начать репетиторство|как быть репетитором|что нужно чтобы стать|должен делать репетитор|зарабатыва.{0,25}репетитор') THEN 'supply_or_recruitment'
  WHEN l.service_id='P20' AND regexp_matches(q.query_normalized, '^(кому нужен|кто нуждается|нужен ли|как выбрать|как проверять)') THEN 'definition'
  WHEN l.service_id='P21' AND regexp_matches(q.query_normalized, '^questions to ask') THEN 'definition'
  WHEN l.service_id='P01' AND starts_with(q.query_normalized,'для какой возрастной категории') THEN 'definition'
  WHEN l.service_id='P13' AND regexp_matches(q.query_normalized, '^wes evaluation services?$') THEN 'specific_official_operator'
  WHEN regexp_matches(q.query_normalized, '(ontario college application service|^ocas\b|^ucas application service$)') THEN 'official_application_provider'
  WHEN regexp_matches(q.query_normalized, '^(what (is|does)|qu.est.ce|w(as|er) ist|que (es|hace)|cos.e|что такое|кто такой|ما هو|什么是)\b') AND
       NOT regexp_matches(q.query_normalized, '(cost|price|fees|prix|preis|precio|tarif|цена|стоимост|сколько стоит|收费|收費|价格|السعر)') THEN 'definition'
  WHEN regexp_matches(q.query_normalized, '(\bjobs?\b|\bsalar(y|ies)\b|ваканси|как стать|как начать (работать|репетитор)|цель репетитор|how to become|training to become|devenir (conseiller|consultant)|puesto de trabajo)') THEN 'supply_or_recruitment'
  WHEN regexp_matches(q.query_normalized, '(sans frais|no (agency )?fees?|без комисси|sin comisi[oó]n|不收[费費]|无需付费)') THEN 'free_or_fee_excluded'
  WHEN l.service_id='P23' AND regexp_matches(q.query_normalized, '(sports coaching|coach personal statement|writer service|essay writing service|write my essay|эссе на заказ|написать за меня|代写|代寫)') THEN 'topic_or_ghostwriting'
  WHEN l.service_id='P20' AND regexp_matches(q.query_normalized, '(practice test book|practice books?|sat prep book)') THEN 'adjacent_goods_or_brand'
  WHEN l.service_id='P20' AND regexp_matches(q.query_normalized, '(100\s*(бал+ь?н|балл|б репетитор)|стобал+ь?н|яндекс репетитор|авито|профи ру|profi ru|skillspace ru|эрик ковалев|умскул|фоксфорд|скайсмарт|schoolhouse|princeton|college board)')
       AND NOT regexp_matches(q.query_normalized, '(price|cost|buy|order|book|цена|цены|стоимость|заказать|купить|оплатить)') THEN 'adjacent_goods_or_brand'
  WHEN l.service_id='P01' AND regexp_matches(q.query_normalized, '(профориентация мгу|^ucas career quiz)') THEN 'institutional_offer'
  ELSE 'kept_rule'
 END AS reason
 FROM queries q JOIN query_labels l USING(query_id)
 WHERE l.evidence_level='D3'
)
SELECT *, CASE WHEN reason='kept_rule' OR starts_with(reason,'reroute_') THEN 'D3' WHEN reason='supply_or_recruitment' THEN 'D0' ELSE 'D1' END AS retained_evidence_level
FROM candidates;

UPDATE query_labels AS l SET
  evidence_level=r.retained_evidence_level,
  relevance=CASE r.reason WHEN 'official_application_provider' THEN 'external_action'
                         WHEN 'adjacent_goods_or_brand' THEN 'navigation'
                         WHEN 'specific_official_operator' THEN 'navigation'
                         WHEN 'supply_or_recruitment' THEN 'outside_purchase'
                         WHEN 'topic_or_ghostwriting' THEN 'outside_purchase'
                         WHEN 'reroute_adviser' THEN 'commercial'
                         WHEN 'reroute_tutoring' THEN 'commercial'
                         ELSE 'relevant' END,
  action_payee=CASE WHEN r.reason IN ('official_application_provider','institutional_offer','specific_official_operator') THEN 'external_institution_or_authority'
    WHEN starts_with(r.reason,'reroute_') THEN 'third_party_service' END,
  service_id=CASE WHEN r.reason='reroute_tutoring' THEN 'P20' WHEN r.reason='reroute_adviser' THEN 'P21'
                  WHEN r.reason IN ('official_application_provider','specific_official_operator','supply_or_recruitment','topic_or_ghostwriting','adjacent_goods_or_brand') THEN NULL
                  ELSE l.service_id END,
  q_id=CASE r.reason WHEN 'official_application_provider' THEN 'Q11' WHEN 'reroute_tutoring' THEN 'Q20'
                     WHEN 'reroute_adviser' THEN 'Q21' ELSE l.q_id END,
  intent_id=CASE r.reason WHEN 'official_application_provider' THEN 'I15'
                         WHEN 'adjacent_goods_or_brand' THEN 'I12'
                         WHEN 'specific_official_operator' THEN 'I12'
                         WHEN 'reroute_tutoring' THEN 'I09' WHEN 'reroute_adviser' THEN 'I09'
                         ELSE 'I01' END,
  cluster_base_id=CASE r.reason WHEN 'official_application_provider' THEN 'K056' WHEN 'reroute_tutoring' THEN 'K095'
                                WHEN 'reroute_adviser' THEN 'K103' ELSE l.cluster_base_id END,
  cluster_id=CASE r.reason WHEN 'official_application_provider' THEN 'K056-I15'
                          WHEN 'adjacent_goods_or_brand' THEN l.cluster_base_id||'-I12'
                          WHEN 'specific_official_operator' THEN l.cluster_base_id||'-I12'
                          WHEN 'reroute_tutoring' THEN 'K095-I09' WHEN 'reroute_adviser' THEN 'K103-I09'
                          ELSE l.cluster_base_id||'-I01' END,
  subcluster_id=CASE r.reason WHEN 'official_application_provider' THEN 'K056-I15'
                             WHEN 'adjacent_goods_or_brand' THEN l.cluster_base_id||'-I12'
                          WHEN 'specific_official_operator' THEN l.cluster_base_id||'-I12'
                          WHEN 'reroute_tutoring' THEN 'K095-I09' WHEN 'reroute_adviser' THEN 'K103-I09'
                             ELSE l.cluster_base_id||'-I01' END
                || substr(l.subcluster_id,length(l.cluster_id)+1),
  task_id=CASE r.reason WHEN 'official_application_provider' THEN 'Q11.06'
             WHEN 'reroute_tutoring' THEN (SELECT TASK_ID FROM cluster_catalog WHERE CLUSTER_BASE_ID='K095')
             WHEN 'reroute_adviser' THEN (SELECT TASK_ID FROM cluster_catalog WHERE CLUSTER_BASE_ID='K103')
             ELSE l.task_id END,
  limitations=coalesce(l.limitations || ' | ', '') || r.reason
FROM commercial_review r WHERE l.query_id=r.query_id AND r.reason<>'kept_rule';
