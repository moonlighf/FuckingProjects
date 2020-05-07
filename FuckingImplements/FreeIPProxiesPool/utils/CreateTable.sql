CREATE TABLE ip_proxies(
    id int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
    ip_address varchar(25) COMMENT 'IP地址',
    port varchar(25) COMMENT '端口',
    http_type varchar(25) comment '类型',
    speed_connect varchar(10) comment '速度',
    time_connect varchar(10) comment '耗时',
    fetch_time date COMMENT '抓取时间'
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
alter table ip_proxies add unique uk_id(`ip_address`, `port`, `http_type`);