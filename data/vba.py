import win32com.client
import path   # 从 path.py 读取目标目录路径

def run_vba_macro(vba_code, macro_name):
    # 启动 Excel
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    # 新建一个工作簿，用来承载宏
    wb = excel.Workbooks.Add()
    vb_module = wb.VBProject.VBComponents.Add(1)  # 1 = 标准模块

    # 插入 VBA 代码
    vb_module.CodeModule.AddFromString(vba_code)

    # 执行宏
    excel.Application.Run(macro_name)

    # 关闭工作簿（不保存）
    wb.Close(SaveChanges=False)
    excel.Quit()


if __name__ == "__main__":
    # VBA 宏代码：递归遍历目录并另存为 MHT
    vba_code = f"""
Sub BatchSaveAsMHTRecursive()
    Dim fso As Object
    Dim folder As Object
    Dim wb As Workbook
    
    Dim rootPath As String
    rootPath = "{path.TARGET_PATH}"
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set folder = fso.GetFolder(rootPath)
    
    ProcessFolder folder
    MsgBox "批量转换完成！"
End Sub

Sub ProcessFolder(f As Object)
    Dim file As Object
    Dim subFolder As Object
    Dim wb As Workbook
    
    For Each file In f.Files
        If LCase(Right(file.Name, 5)) = ".xlsx" Then
            If Left(file.Name, 2) <> "~$" Then
                Set wb = Workbooks.Open(file.Path)
                wb.SaveAs Replace(file.Path, ".xlsx", ".mht"), FileFormat:=45
                wb.Close SaveChanges:=False
            End If
        End If
    Next
    
    For Each subFolder In f.SubFolders
        ProcessFolder subFolder
    Next
End Sub
"""

    run_vba_macro(vba_code, "BatchSaveAsMHTRecursive")
