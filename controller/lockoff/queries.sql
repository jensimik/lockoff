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

-- name: get_active_users_by_mobile
-- get active users by mobile number
select user_id, name, member_type, mobile, email, batch_id, active
  from users
 where mobile = :mobile and active = true;

-- name: get_active_users_by_user_id_mobile
-- get active users by mobile number
select user_id, name, member_type, mobile, email, batch_id, active
  from users
 where user_id = :user_id and mobile = :mobile and active = true;


-- name: update_user_set_totp_secret!
-- update users by mobile and set totp_secret
update users
set totp_secret = :totp_secret
where mobile = :mobile;

-- name: upsert_user!
-- upsert a user in the database
insert into users(user_id, name, member_type, mobile, email, batch_id, active)
values (:user_id, :name, :member_type, :mobile, :email, :batch_id, :active)
on conflict(user_id) do 
update set name=excluded.name, member_type=excluded.member_type, mobile=excluded.mobile, email=excluded.email, batch_id=excluded.batch_id, active=excluded.active;

-- name: bulk_upsert_user*!
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

-- name: get_dayticket_by_id^
-- get a dayticket by id
select ticket_id, expires
from dayticket
where ticket_id = :ticket_id;

-- name: update_dayticket_expire!
-- update a dayticket to expire at x time
update dayticket
set expires = :expires
where ticket_id = :ticket_id;

-- name: log_entry!
-- log an entry on the door
insert into access_log(user_id, token_type, timestamp)
values (:user_id, :token_type, :timestamp);

-- name: init_db#
-- initialize the databases
create table if not exists users (
    user_id integer not null primary key,
    name text not null,
    member_type text not null,
    mobile text not null,
    email text not null,
    batch_id text not null,
    totp_secret text not null default ""
    active bool not null
);
create table if not exists access_log (
    log_id integer not null primary key,
    user_id integer not null,
    token_type text not null,
    timestamp text not null,
);
create table if not exists dayticket (
    ticket_id integer not null primary key,
    expires integer nul null
);