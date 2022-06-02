from datetime import datetime
from datetime import timezone
import math
import time
def to360range(num):
      if ( num > 360 ):
           return num - math.floor( num / 360 ) * 360 
      elif ( num < 0 ):
           return num + ( math.floor( - num / 360 ) + 1 ) * 360
      else:
           return num
def get_angle(coordx,coordy,date:datetime,diff):
    m = date.month
    y = date.year
    d = 367 * y - math.floor( ( 7 * ( y + ( math.floor( ( m + 9 ) / 12 ) ) ) ) / 4 ) + math.floor( ( 275 * m ) / 9 ) + date.day - 730530
    w = 282.9404 + 4.70935 * math.pow( 10, - 5 ) * d
    e = 0.016709 - 1.151 * math.pow( 10, - 9 ) * d
    M = to360range( 356.0470 + 0.9856002585 * d )
    oblecl = 23.4393 - 3.563 * math.pow( 10, - 7 ) * d
    L = to360range( w + M )
    E = M + ( 180 / math.pi ) * e * math.sin( M * math.pi / 180 ) * ( 1 + e * math.cos( M * math.pi / 180 ) )

    x = math.cos( E * math.pi / 180 ) - e
    y = math.sin( E * math.pi / 180 ) * math.sqrt( 1 - e * e )
    r = math.sqrt( x * x + y * y )
    v = ( 180 / math.pi ) * math.atan2( y, x )
    lon = to360range( v + w )

    x = r * math.cos( lon * math.pi / 180 )
    y = r * math.sin( lon * math.pi / 180 )
    z = 0.0
    xequat = x
    yequat = y * math.cos( oblecl * math.pi / 180 ) + z * math.sin( oblecl * math.pi / 180 )
    zequat = y * math.sin( oblecl * math.pi / 180 ) + z * math.cos( oblecl * math.pi / 180 )

    RA = ( 180 / math.pi ) * math.atan2( yequat, xequat )
    Decl = ( 180 / math.pi ) * math.asin( zequat / r )

    GMST0 = L / 15 + 12
    utdate = date.astimezone(timezone.utc)
    UT = utdate.hour + utdate.minute / 60
    SIDTIME = GMST0 + UT + coordy / 15
    SIDTIME = SIDTIME - 24 * math.floor( SIDTIME / 24 )
    HA = to360range( 15 * ( SIDTIME - RA / 15 ) )
    x = math.cos( HA * math.pi / 180 ) * math.cos( Decl * math.pi / 180 )
    y = math.sin( HA * math.pi / 180 ) * math.cos( Decl * math.pi / 180 )
    z = math.sin( Decl * math.pi / 180 )
    xhor = x * math.sin( coordx * math.pi / 180 ) - z * math.cos( coordx * math.pi / 180 )
    yhor = y
    zhor = x * math.cos( coordx * math.pi / 180 ) + z * math.sin( coordx * math.pi / 180 )
    azimuth = ( to360range( math.atan2( yhor, xhor ) * ( 180 / math.pi ) + 180 ) )
    altitude = ( math.asin( zhor ) * ( 180 / math.pi ) )

    return (azimuth,altitude)
date = datetime.fromtimestamp(time.time())