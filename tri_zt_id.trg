create or replace trigger tri_zt_id
  before insert on table_name  
  for each row
declare
  -- local variables here
begin
  select SEQ_ZT_ID.nextval into :new.ID from dual;
end tri_zt_id;
/
