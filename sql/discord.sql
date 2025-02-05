create table discord_interaction
(
    interaction_id      int auto_increment comment 'primary key',
    message_id          bigint                     not null comment '消息Id',
    channel_id          bigint                     not null comment '频道Id',
    user_id             bigint                     not null comment '用户Id',
    username            varchar(256)               not null comment '用户名',
    interaction_content text                       not null comment '发言内容',
    interaction_time    timestamp                  not null comment '发言时间',
    post_time           timestamp                  not null comment '帖子发布时间',
    collect_time        timestamp    default now() not null comment '采集时间',
    note                varchar(256) null comment '备注',
    type                tinyint(1)              not null comment '发言类型 (1:文字 | 2:点赞 ｜ 转发)',
    is_published        tinyint(1)              not null comment '是否已发布 (1:已发布 | 0:未发布)',
    nostr_event_id      varchar(256) default '' null comment 'Nostr Event Id',
    constraint discord_interaction_pk
        primary key (interaction_id)
) comment '发言消息表';

create index idx_channelId_userId
    on discord_interaction (channel_id, user_id);



create table discord_channel_collect_log
(
    id                    bigint auto_increment comment '主键',
    channel_id            bigint                  not null comment '频道Id',
    collect_time          timestamp default now() not null comment '采集时间',
    collect_start_time    timestamp null comment '本次采集时间区间(开始)',
    collect_end_time      timestamp null comment '本次采集时间区间(结束)',
    collect_message_count int       default 0     not null comment '采集消息数',
    collect_status        tinyint(1)              not null comment '采集是否成功 (1:成功 | 0:失败 | 2:采集进行中)',
    collect_error_message text null comment '采集失败原因',
    constraint discord_channel_collect_log_pk
        primary key (id)
) comment '频道消息采集日志表';

create index idx_channelId_collectTime
    on discord_channel_collect_log (channel_id asc, collect_time desc);


create table discord_channel
(
    id                 int auto_increment comment '主键'
        primary key,
    channel_id         bigint                              not null comment '频道Id',
    collect_start_time timestamp null comment '采集开始时间',
    collect_end_time   timestamp null comment '采集结束时间',
    update_frequency   varchar(10) null comment '互动数据更新频率 (10m:十分钟, 1h:一小时, 2d:两天) ',
    expiration_time    varchar(10) null comment '互动数据过期时间 (如1w:一周,1m:一个月,1y:一年)',
    create_at          timestamp default CURRENT_TIMESTAMP not null comment '创建时间',
    update_at          timestamp default CURRENT_TIMESTAMP not null comment '更新时间'
);

create index idx_channelId
    on discord_channel (channel_id);

