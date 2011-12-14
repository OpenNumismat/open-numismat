library Cdr2Xml;

uses ShareMem, MidasLib, CRTL, Forms, DBClient;

procedure CdrToXml(_src, _dst: PWideChar; _format: Integer); stdcall;
var
table : TClientDataset;
begin
  table := TClientDataset.Create(Application);
  table.LoadFromFile(string(_src));
  table.SaveToFile(string(_dst), TDataPacketFormat(_format));
end;

exports CdrToXml;

begin
end.

