-- Primary query-to-conversion association. Full provider records remain in observations.
create or replace view query_journey as
select q.query_id,
       q.query_raw, q.query_normalized, coalesce(l.query_translation,qt.query_translation,case when l.language='ru' then q.query_raw end) as query_translation,
       l.language, q.search_market, l.destination_hint as destination, q.search_engine,
       q.source_id, q.source_url, q.export_date as source_date, q.volume, q.cpc, q.kd,
       l.intent_id, l.cluster_id, l.subcluster_id, l.q_id, l.task_id, s.cjm_id,
       l.service_id, coalesce(cv.product_id,s.product_id) as product_id,
       cv.page_type, cv.page_url_pattern, cv.element_id,
       coalesce(loc.cta_primary,cv.cta_primary) as cta_primary,
       coalesce(loc.cta_secondary,cv.cta_secondary) as cta_secondary,
       cv.cta_trigger, cv.cta_target, cv.free_value, cv.paid_value, cv.payment_type, cv.fulfilment,
       cv.event, cv.kpi, coalesce(l.evidence_level,'D0') as evidence_level, l.confidence,
       nullif(concat_ws(' | ',
           case when q.search_market is null then 'география поиска не определена' end,
           case when l.cluster_id is null then 'нет надёжной классификации' end,
           case when l.service_id is not null and cv.conversion_id is null then 'нет интерфейса' end,
           case when l.cluster_id is not null and l.task_id is null then 'нет 1:1 соответствия листу v2' end,
           case when l.language is not null and cv.conversion_id is not null and loc.language is null then 'требуется локализация CTA' end
       ),'') as gap,
       q.source_region, q.unknown_scope, q.observed_date, q.volume_metric, q.target_url,
       q.observation_count, q.source_count, q.language_raw,
       l.cluster_base_id, l.relevance, l.secondary_clusters, l.learning_level, l.program_type, l.role,
       cv.conversion_id, r.fallback_conversion_id, r.post_result_conversion_id,
       l.action_payee, l.language_source, cv.route_kind, cv.cta_placement, cv.target_action, cv.inputs, cv.test_method, r.activation_rule
from queries q join query_labels l using(query_id)
left join query_translations qt using(query_normalized)
left join services s on l.service_id=s.service_id
left join conversion_intents r on l.service_id=r.service_id and l.intent_id=r.intent_id
left join (select * from conversions union all by name select * from neutral_conversions) cv on
  case when l.action_payee='external_institution_or_authority' and l.intent_id='I15' then 'C-neutral-official'
       when l.intent_id='I12' then 'C-neutral-nav'
       when l.intent_id='I14' then 'C-neutral-resume'
       when l.service_id is null and l.cluster_id is not null then 'C-neutral-answer'
       when l.evidence_level is distinct from 'D3' then coalesce(r.fallback_conversion_id,r.conversion_id)
       else r.conversion_id end = cv.conversion_id
left join (select * from cta_localizations union all by name select * from neutral_cta_localizations) loc on loc.conversion_id=cv.conversion_id and
  loc.language=(case when l.language='zh' then case when q.search_market in ('HK','TW','MO') then 'zh-Hant' else 'zh-Hans' end
                     else l.language end);

create or replace view cluster_instances as
select cluster_id, any_value(cluster_base_id) cluster_base_id, any_value(q_id) q_id,
       any_value(task_id) task_id, any_value(intent_id) intent_id, any_value(service_id) service_id,
       count(*) unique_queries, count(*) filter (where evidence_level='D3') d3_queries
from query_journey where cluster_id is not null group by cluster_id;

create or replace view regional_subclusters as
select subcluster_id, any_value(cluster_id) cluster_id, any_value(search_market) search_market,
       any_value(language) language, count(*) unique_queries
from query_journey where subcluster_id is not null group by subcluster_id;
