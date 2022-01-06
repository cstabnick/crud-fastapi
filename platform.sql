SET TIMEZONE='America/New_York';

;drop table if exists users;

create table users (user_id bigint not null,
	email text not null,
	username text not null,
	password bytea not null,
	created_at timestamptz not null,
	updated_at timestamptz not null,
	is_deleted bool not null,
	primary key (user_id)
);

create index ix_users_username_password on users(username, password, user_id);

create or replace function id_gen()
	   returns bigint 
   language plpgsql
  as
$$
declare 
	new_id bigint;
begin
	  -- include info such as db this is running on?
	select ((random() * 2^62 / 10000)::decimal(15, 0)::text || '0009')::bigint
	into new_id;
	
	return new_id;
end;
$$
;


create or replace function does_id_exist(id bigint, tbl text)
	   returns bool 
   language plpgsql
  as
$$
declare 
	does_exist bool;
begin
	execute 'select count(*) > 0 from ' || tbl 
		|| ' where ' || left(tbl, length(tbl) - 1) || '_id = ' || id
	into does_exist;
	
	return does_exist;
end;
$$
;


create or replace function new_id(tbl text)
	   returns bigint
   language plpgsql
  as
$$
declare 
	new_id bigint;
	
begin
	  -- include info such as db this is running on?
	select id_gen()
	into new_id;
	
	if (does_id_exist(new_id, tbl)) then 
		-- shouldnt ever happen, if so we can catch and retry?
		select id_gen()
		into new_id;
		
		if (does_id_exist(new_id, tbl)) then
			-- REALLY shouldnt ever happen
			raise  'Something went wrong please try again';
		end if;
	end if;

	return new_id;
end;
$$
;
select * from users;


drop table if exists sessions;
create table sessions (session_id bigint not null primary key, user_id bigint not null, created_at timestamptz, expires_at timestamptz)
;

create index ix_sessions_expires_at_desc on sessions(expires_at desc);




select new_id('sessions');




-- below here doesnt work 
drop function if exists update_session;
create or replace function update_session(in_user_id bigint)
	   returns bigint -- session_id
   language plpgsql
  as
$$
declare 
	s_id bigint;
begin
	if (	
			select count(*) 
			from sessions s 
			where s.user_id = in_user_id
			and now() < expires_at 
		) > 0 then 

		select s.session_id 
		from sessions s 
		where s.user_id = in_user_id 
		order by expires_at desc 
		limit 1
		into s_id;
		
		update sessions 
		set expires_at = now() + '00:30:00'
		where session_id = s_id;
		return s_id;
	end if;

	select new_id('sessions') into s_id;

	insert into sessions(session_id, user_id, created_at, expires_at)
	select s_id, in_user_id, now(), now() + '00:30:00' ;

	return s_id;
end;
$$
;




create unique index ixu_users_email on users(email);


select * from sessions s order by expires_at desc;

select * from users u	



