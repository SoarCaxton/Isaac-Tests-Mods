import win32com.client
import path   # 从 path.py 读取目标目录路径

def run_vba_macro(vba_code, macro_name):
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    wb = excel.Workbooks.Add()
    vb_module = wb.VBProject.VBComponents.Add(1)  # 1 = 标准模块
    vb_module.CodeModule.AddFromString(vba_code)

    excel.Application.Run(macro_name)

    wb.Close(SaveChanges=False)
    excel.Quit()


if __name__ == "__main__":
    vba_code = f"""
Sub BatchSaveAsHTMLRecursive()
    Dim fso As Object
    Dim folder As Object
    Dim wb As Workbook
    Dim dict As Object
    Dim indexPath As String
    Dim f As Integer
    
    Dim rootPath As String
    rootPath = "{path.TARGET_PATH}"
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set folder = fso.GetFolder(rootPath)
    Set dict = CreateObject("Scripting.Dictionary")
    
    ProcessFolder folder, rootPath, dict
    
    ' 生成 index.html
    indexPath = rootPath & "\\index.html"
    f = FreeFile
    Open indexPath For Output As #f
    Print #f, "<html><head><meta charset='utf-8'><title>Excel 2 HTML</title></head><body>"
    Print #f, "<h1>Excel 2 HTML</h1>"
    
    Dim key As Variant
    For Each key In dict.Keys
        Print #f, "<h2>" & key & "</h2><ul>"
        Dim files As Variant
        files = dict(key)
        Dim i As Integer
        For i = LBound(files) To UBound(files)
            Print #f, "<li><a href='" & files(i) & "' target='_blank'>" & files(i) & "</a></li>"
        Next
        Print #f, "</ul>"
    Next
    
    Print #f, "</body></html>"
    Close #f
    
    MsgBox "批量转换完成！索引文件已生成: " & indexPath
End Sub

Sub ProcessFolder(f As Object, rootPath As String, dict As Object)
    Dim file As Object
    Dim subFolder As Object
    Dim wb As Workbook
    Dim relPath As String
    Dim folderName As String
    Dim files() As String
    Dim count As Integer
    
    folderName = Replace(f.Path, rootPath & "\\", "")
    If folderName = "" Then folderName = "(根目录)"
    
    count = 0
    
    For Each file In f.Files
        If LCase(Right(file.Name, 5)) = ".xlsx" Then
            If Left(file.Name, 2) <> "~$" Then
                Set wb = Workbooks.Open(file.Path)
                wb.SaveAs Replace(file.Path, ".xlsx", ".html"), FileFormat:=44
                wb.Close SaveChanges:=False
                relPath = Replace(file.Path, rootPath & "\\", "")
                relPath = Replace(relPath, ".xlsx", ".html")
                relPath = Replace(relPath, "\\", "/") ' 转换为网页路径格式
                ReDim Preserve files(count)
                files(count) = relPath
                count = count + 1
            End If
        End If
    Next
    
    If count > 0 Then
        dict(folderName) = files
    End If
    
    For Each subFolder In f.SubFolders
        ProcessFolder subFolder, rootPath, dict
    Next
End Sub
"""

    run_vba_macro(vba_code, "BatchSaveAsHTMLRecursive")
