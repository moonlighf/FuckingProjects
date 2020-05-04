CREATE TABLE fund_profit(
    id int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
    fund_name varchar(45) COMMENT '基金名',
    fund_num varchar(45) COMMENT '基金编号',
    fund_type varchar(45) COMMENT '基金类型',
    new_value varchar(95) COMMENT '最新净值',
    new_value_day date COMMENT '最新净值日期',
    profit_near_week varchar(25) COMMENT '近一周收益率',
    profit_near_month varchar(25) COMMENT '近一月收益率',
    profit_near_three_month varchar(25) COMMENT '近三个月收益率',
    profit_near_six_month varchar(25) COMMENT '近六个月收益率',
    profit_near_year varchar(25) COMMENT '近一年收益率',
    profit_near_two_year varchar(25) COMMENT '近两年收益率',
    profit_near_three_year varchar(25) COMMENT '近三年收益率',
    detail_url varchar(95) COMMENT '基金详情页',
    fetch_time date COMMENT '抓取时间'
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
alter table fund_profit add unique uk_id(`fund_num`, `fund_type`, `new_value_day`);