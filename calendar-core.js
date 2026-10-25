import ICAL from './vendor/ical.js';
const localDate=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const localTime=d=>`${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
export function asDate(time,event){const tz=event.component.getFirstProperty('dtstart')?.getParameter('tzid');if(time.isDate||!tz||time.zone!==ICAL.Timezone.localTimezone||tz==='UTC')return time.toJSDate();
 let guess=Date.UTC(time.year,time.month-1,time.day,time.hour,time.minute,time.second),wanted=guess;
 const fmt=new Intl.DateTimeFormat('en-GB',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
 for(let i=0;i<4;i++){const p=Object.fromEntries(fmt.formatToParts(new Date(guess)).map(p=>[p.type,p.value]));const seen=Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute,+p.second);const delta=wanted-seen;if(!delta)break;guess+=delta}return new Date(guess)}
export async function parseCalendar(text,sourceId,now=new Date()){
 if(typeof text!=='string'||text.length>2*1024*1024)throw Error('Calendar exceeds the 2 MB limit.');
 let root;try{root=new ICAL.Component(ICAL.parse(text))}catch{throw Error('This is not a valid iCalendar file.');}
 if(root.name!=='vcalendar')throw Error('Expected an iCalendar calendar.');
 for(const zone of root.getAllSubcomponents('vtimezone')){const tzid=zone.getFirstPropertyValue('tzid');if(tzid)ICAL.TimezoneService.register(tzid,new ICAL.Timezone({component:zone,tzid}))}
 const lower=new Date(now);lower.setDate(lower.getDate()-90);lower.setHours(0,0,0,0);const upper=new Date(now);upper.setDate(upper.getDate()+366);upper.setHours(0,0,0,0);
 const components=root.getAllSubcomponents('vevent');if(components.length>5000)throw Error('Too many events. Use a smaller calendar.');
 const byUid=new Map();for(const c of components){const uid=c.getFirstPropertyValue('uid');if(!uid)throw Error('An event is missing its UID.');if(!byUid.has(uid))byUid.set(uid,[]);byUid.get(uid).push(c)}
 const occurrences=[];let steps=0;
 async function add(event,original,start,end){if(event.component.getFirstPropertyValue('status')==='CANCELLED')return;const from=asDate(start,event),to=asDate(end,event);if(to<lower||from>=upper)return;const label=String(event.summary||'Untitled event').slice(0,200);let cursor=new Date(Math.max(from.getTime(),lower.getTime()));cursor.setHours(0,0,0,0);let segments=0;
 while(cursor<upper&&(cursor<to||(+cursor===+to&&+from===+to))){if(++segments>400)throw Error('Event duration is too long.');const next=new Date(cursor);next.setDate(next.getDate()+1);const a=new Date(Math.max(+from,+cursor)),b=new Date(Math.min(+to,+next));const date=localDate(cursor);const key=`${sourceId}|${event.uid}|${original}|${date}`;const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(key));const id='ical_'+Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');occurrences.push({id,title:label,date,time:start.isDate?'00:00':localTime(a),end:+b===+next?'23:59':localTime(b),allDay:start.isDate,location:String(event.location||'').slice(0,300),sourceId});if(occurrences.length>5000)throw Error('Too many occurrences. Use a smaller calendar.');cursor=next}
 }
 for(const [uid,group] of byUid){const base=group.find(c=>!c.hasProperty('recurrence-id'));const exceptions=group.filter(c=>c.hasProperty('recurrence-id')).map(c=>new ICAL.Event(c));if(!base){for(const e of exceptions)await add(e,e.recurrenceId?.toString()||e.startDate.toString(),e.startDate,e.endDate);continue}const event=new ICAL.Event(base,{exceptions});if(base.getFirstPropertyValue('status')==='CANCELLED')continue;if(event.isRecurring()){const iterator=event.iterator();let time;while((time=iterator.next())){if(++steps>60000)throw Error('This recurrence is too large to expand safely.');if(asDate(time,event)>=upper)break;const details=event.getOccurrenceDetails(time);await add(details.item,time.toString(),details.startDate,details.endDate)}}else await add(event,event.startDate.toString(),event.startDate,event.endDate);
 // Moved exceptions may cross the expansion boundary; include them explicitly and deduplicate.
 for(const exception of exceptions)await add(exception,exception.recurrenceId.toString(),exception.startDate,exception.endDate);
 }
 return {name:String(root.getFirstPropertyValue('x-wr-calname')||'Imported calendar').slice(0,100),occurrences:[...new Map(occurrences.map(e=>[e.id,e])).values()],from:localDate(lower),until:localDate(upper)};
}
if(typeof window!=='undefined')window.PlannerCalendar={parseCalendar};
