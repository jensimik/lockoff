-- name: stats
-- get some stats
select email, count(*) as count
from users
group by email
having count > 1;

-- name: get_all_users
-- Get all the users in the database
select user_id, name, member_type, mobile, email, batch_id, active
from users
order by 1;

-- name: get_user_by_user_id^
-- Get a user by user id
select user_id, name, member_type, mobile, email, batch_id, active
from users
where user_id = :user_id;

-- name: get_active_user_by_user_id^
-- Get a user by user id
select user_id, name, member_type, mobile, email, batch_id, active
from users
where user_id = :user_id and active = true;

-- name: get_active_users_by_user_ids
-- get active users by user_ids
select user_id, name, member_type, mobile, email, batch_id, totp_secret, active
from users
where user_id in (:user_ids) and active = true;

-- name: get_active_users_by_mobile
-- get active users by mobile number
select user_id, name, member_type, mobile, email, batch_id, totp_secret, active
from users
where mobile = :mobile and active = true;

-- name: get_active_users_by_email
-- get active users by mobile number
select user_id, name, member_type, mobile, email, batch_id, totp_secret, active
from users
where email = :email and active = true;

-- name: get_active_users_by_mobile_or_email
-- get active users by email or mobile number
select user_id, name, member_type, mobile, email, batch_id, totp_secret, active
from users
where (email = :username or mobile = :username) and active = true;


 -- name: get_active_user_totp_secret_by_mobile$
select totp_secret
from users
where mobile = :mobile and active = true;


-- name: get_active_user_by_user_id^
-- get active users by mobile number
select user_id, name, member_type, mobile, email, batch_id, active
from users
where user_id = :user_id and active = true;


-- name: update_user_by_mobile_set_totp_secret!
-- update users by mobile and set totp_secret
update users
set totp_secret = :totp_secret
where mobile = :mobile;

-- name: update_user_by_email_set_totp_secret!
-- update users by mobile and set totp_secret
update users
set totp_secret = :totp_secret
where email = :email;

-- name: get_last_klubmodul_sync$
-- get the last isoformat datetime klubmodul were synced (last batchid)
select max(batch_id)
from users
where active == True

-- name: count_active_users$
-- count active users
select count(*)
from users
where active == True

-- name: upsert_user!
-- upsert a user in the database
insert into users(user_id, name, member_type, mobile, email, batch_id, active)
values (:user_id, :name, :member_type, :mobile, :email, :batch_id, :active)
on conflict(user_id) do 
update set name=excluded.name, member_type=excluded.member_type, mobile=excluded.mobile, email=excluded.email, batch_id=excluded.batch_id, active=excluded.active;

-- name: inactivate_old_batch!
-- inactivate old batches
update users 
set active = false
where batch_id != :batch_id;

-- name: insert_dayticket<!
-- insert a new dayticket with no expire time set yet
insert into dayticket(batch_id, expires)
values (:batch_id, 0)

-- name: get_dayticket_by_id^
-- get a dayticket by id
select ticket_id, expires
from dayticket
where ticket_id = :ticket_id;

-- name: get_dayticket_stats
-- get stats about dayticket batches
select batch_id, min(dayticket_id) as range_start, max(dayticket_id) as range_end, SUM(CASE WHEN expires = 0 THEN 1 ELSE 0 END) as unused,  SUM(CASE WHEN expires > 0 THEN 1 ELSE 0 END) as used
from dayticket
group by batch_id

-- name: update_dayticket_expire!
-- update a dayticket to expire at x time
update dayticket
set expires = :expires
where ticket_id = :ticket_id;

-- name: log_entry!
-- log an entry on the door
insert into access_log(user_id, token_type, timestamp)
values (:user_id, :token_type, :timestamp);

-- name: last_log_entries
-- get last :limit log entries
select log_id, user_id, token_type, timestamp
from access_log
order by timestamp desc
limit :limit;

-- name: create_schema#
-- initialize the databases
create table if not exists users (
    user_id integer not null primary key,
    name text not null,
    member_type text not null,
    mobile text not null,
    email text not null,
    batch_id text not null,
    totp_secret text not null default "",
    active integer not null
);
create table if not exists access_log (
    log_id integer not null primary key,
    user_id integer not null,
    token_type text not null,
    timestamp text not null
);
create table if not exists dayticket (
    ticket_id integer not null primary key,
    batch_id text not null,
    expires integer not null
);